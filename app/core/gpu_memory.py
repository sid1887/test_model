"""
Hybrid GPU/CPU Memory Management for AI Models
Optimized for GT 710 (2GB VRAM) with intelligent device switching
"""

import torch
import gc
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Union
import psutil
import time
from dataclasses import dataclass, field
import warnings
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DeviceStats:
    """Track device performance and failures"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_inference_time: float = 0.0
    memory_errors: int = 0
    last_failure_time: float = 0.0
    consecutive_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_operations == 0:
            return 1.0
        return self.successful_operations / self.total_operations
    
    @property
    def failure_rate(self) -> float:
        return 1.0 - self.success_rate
    
    def reset_failures(self):
        """Reset failure counters"""
        self.failed_operations = 0
        self.consecutive_failures = 0
        self.memory_errors = 0


class HybridGPUMemoryManager:
    """Intelligent GPU/CPU memory manager optimized for GT 710 and low-end GPUs"""
    
    def __init__(self, gpu_memory_limit_gb: Optional[float] = None, 
                 memory_threshold: float = 0.7, 
                 cleanup_interval: int = 10):
        """
        Initialize the memory manager
        
        Args:
            gpu_memory_limit_gb: Manual GPU memory limit in GB (auto-detected if None)
            memory_threshold: Memory usage threshold (0.0-1.0)
            cleanup_interval: Operations between cleanup cycles
        """
        self.gpu_available = torch.cuda.is_available()
        self.device_stats = {
            "cuda": DeviceStats(),
            "cpu": DeviceStats()
        }
        
        # Configuration
        self.memory_threshold = max(0.1, min(1.0, memory_threshold))
        self.max_consecutive_failures = 3
        self.failure_cooldown = 300  # 5 minutes before retrying GPU
        self.cleanup_interval = max(1, cleanup_interval)
        
        # Performance tracking
        self.operation_count = 0
        self.last_cleanup_time = time.time()
        self.forced_cpu_mode = False
        self.forced_cpu_until = 0.0
        
        # Initialize GPU info and settings
        if self.gpu_available:
            self.gpu_info = self._analyze_gpu_capabilities()
            if gpu_memory_limit_gb is not None:
                self.gpu_memory_limit = max(0.5, gpu_memory_limit_gb)
            self._setup_gpu_optimizations()
            logger.info(f"🎮 GPU initialized: {self.gpu_info['name']} "
                       f"({self.gpu_info['total_memory_gb']:.1f}GB, "
                       f"limit: {self.gpu_memory_limit:.1f}GB)")
        else:
            self.gpu_info = None
            self.gpu_memory_limit = 0.0
            logger.info("💻 Running in CPU-only mode (no GPU detected)")
    
    def _analyze_gpu_capabilities(self) -> Dict[str, Any]:
        """Analyze GPU capabilities and set appropriate limits"""
        try:
            device = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device)
            total_memory_gb = props.total_memory / (1024**3)
            device_name = torch.cuda.get_device_name(device)
            
            # Detect low-end GPUs by name patterns
            low_end_patterns = [
                'gt 610', 'gt 710', 'gt 720', 'gt 730', 'gt 740', 'gt 1030',
                'gtx 1050', 'gtx 1650', 'gtx 1060 3gb', 'mx150', 'mx250', 'mx350',
                'intel', 'radeon r5', 'radeon r7', 'vega 8', 'vega 11'
            ]
            
            device_lower = device_name.lower()
            is_low_end = (any(pattern in device_lower for pattern in low_end_patterns) or 
                         total_memory_gb < 4)
            
            # Set conservative limits based on GPU type
            if is_low_end or total_memory_gb < 4:
                self.gpu_memory_limit = min(1.2, total_memory_gb * 0.6)
                strategy = "conservative"
                recommended_batch_size = 1
            elif total_memory_gb < 8:
                self.gpu_memory_limit = total_memory_gb * 0.75
                strategy = "moderate"
                recommended_batch_size = 2
            else:
                self.gpu_memory_limit = total_memory_gb * 0.85
                strategy = "aggressive"
                recommended_batch_size = 4
            
            return {
                'name': device_name,
                'total_memory_gb': total_memory_gb,
                'usable_memory_gb': self.gpu_memory_limit,
                'is_low_end': is_low_end,
                'strategy': strategy,
                'compute_capability': f"{props.major}.{props.minor}",
                'multiprocessor_count': props.multiprocessor_count,
                'recommended_batch_size': recommended_batch_size,
                'device_id': device
            }
            
        except Exception as e:
            logger.error(f"GPU analysis failed: {e}")
            self.gpu_memory_limit = 1.0  # Fallback to 1GB limit
            return {
                'error': str(e), 
                'name': 'Unknown GPU', 
                'total_memory_gb': 2.0,
                'usable_memory_gb': 1.0,
                'is_low_end': True,
                'strategy': 'conservative'
            }
    
    def _setup_gpu_optimizations(self):
        """Setup GPU-specific optimizations"""
        if not self.gpu_available:
            return
            
        try:
            # Set memory fraction for better control
            memory_fraction = min(0.9, self.gpu_memory_limit / self.gpu_info['total_memory_gb'])
            if hasattr(torch.cuda, 'set_memory_fraction'):
                torch.cuda.set_memory_fraction(memory_fraction)
                logger.debug(f"GPU memory fraction set to {memory_fraction:.2f}")
            
            # Optimize CUDNN settings
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.enabled = True
            
            # Enable TensorFloat-32 if supported (Ampere and newer)
            if hasattr(torch.backends.cuda.matmul, 'allow_tf32'):
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                
            # Initial cleanup
            torch.cuda.empty_cache()
            
        except Exception as e:
            logger.warning(f"GPU optimization setup failed: {e}")
    
    def should_use_gpu(self, estimated_memory_mb: float = 500) -> bool:
        """Intelligently decide whether to use GPU based on current state"""
        if not self.gpu_available:
            return False
        
        # Check if forced CPU mode is active
        if self.forced_cpu_mode and time.time() < self.forced_cpu_until:
            remaining = self.forced_cpu_until - time.time()
            logger.debug(f"Forced CPU mode active for {remaining:.0f}s more")
            return False
        elif self.forced_cpu_mode and time.time() >= self.forced_cpu_until:
            self.forced_cpu_mode = False
            logger.info("Forced CPU mode expired, GPU re-enabled")
        
        # Check consecutive failure count and cooldown
        cuda_stats = self.device_stats["cuda"]
        if cuda_stats.consecutive_failures >= self.max_consecutive_failures:
            time_since_failure = time.time() - cuda_stats.last_failure_time
            if time_since_failure < self.failure_cooldown:
                logger.debug(f"GPU in cooldown for {self.failure_cooldown - time_since_failure:.0f}s")
                return False
            else:
                # Reset consecutive failures after cooldown
                cuda_stats.consecutive_failures = 0
                logger.info("GPU cooldown expired, retrying GPU operations")
        
        try:
            # Check current GPU memory usage
            allocated_gb = torch.cuda.memory_allocated() / (1024**3)
            reserved_gb = torch.cuda.memory_reserved() / (1024**3)
            estimated_needed_gb = estimated_memory_mb / 1024
            
            current_usage = max(allocated_gb, reserved_gb)
            projected_usage = current_usage + estimated_needed_gb
            
            # Decision based on memory availability
            memory_limit_with_threshold = self.gpu_memory_limit * self.memory_threshold
            if projected_usage > memory_limit_with_threshold:
                logger.debug(f"GPU memory insufficient: {projected_usage:.2f}GB needed, "
                           f"{memory_limit_with_threshold:.2f}GB available")
                return False
            
            # Check success rate (only if we have enough data)
            if cuda_stats.total_operations >= 5 and cuda_stats.success_rate < 0.6:
                logger.debug(f"GPU success rate too low: {cuda_stats.success_rate:.2f}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"GPU availability check failed: {e}")
            self._record_failure("cuda", "memory_check_error")
            return False
    
    def get_optimal_device(self, model_type: str = "default", 
                          estimated_memory_mb: Optional[float] = None) -> str:
        """Get optimal device for inference with model-specific considerations"""
        
        # Model-specific memory estimates (MB)
        model_memory_estimates = {
            "yolo": 600,
            "yolov5": 500,
            "yolov8": 700,
            "clip": 400,
            "efficientnet": 300,
            "resnet": 350,
            "mobilenet": 200,
            "bert": 500,
            "gpt": 800,
            "transformer": 600,
            "default": 500
        }
        
        if estimated_memory_mb is None:
            estimated_memory_mb = model_memory_estimates.get(model_type.lower(), 500)
        
        if self.should_use_gpu(estimated_memory_mb):
            return "cuda"
        else:
            return "cpu"
    
    @contextmanager
    def managed_inference(self, model_name: str = "Unknown", 
                         model_type: str = "default",
                         estimated_memory_mb: Optional[float] = None):
        """Context manager for intelligent device-managed inference"""
        start_time = time.time()
        device = self.get_optimal_device(model_type, estimated_memory_mb)
        original_device = device
        inference_successful = False
        
        # Pre-inference setup
        if device == "cuda" and self.gpu_available:
            try:
                initial_memory = torch.cuda.memory_allocated() / (1024**3)
                logger.debug(f"🎮 {model_name} using GPU - Memory: {initial_memory:.2f}GB")
            except:
                logger.debug(f"🎮 {model_name} using GPU")
        else:
            logger.debug(f"💻 {model_name} using CPU")
        
        try:
            yield device
            inference_successful = True
            
            # Record successful operation
            inference_time = time.time() - start_time
            self._record_success(device, inference_time)
            
        except torch.cuda.OutOfMemoryError as e:
            logger.warning(f"GPU OOM for {model_name}: {str(e)[:100]}...")
            self._record_failure(device, "out_of_memory")
            
            # Try CPU fallback if we were using GPU
            if device == "cuda" and not inference_successful:
                logger.info(f"🔄 Falling back to CPU for {model_name}")
                self._aggressive_gpu_cleanup()
                device = "cpu"
                yield device
                inference_time = time.time() - start_time
                self._record_success("cpu", inference_time)
                inference_successful = True
            else:
                raise
                
        except Exception as e:
            if not inference_successful:
                self._record_failure(device, "inference_error")
                logger.error(f"Inference failed for {model_name} on {device}: {str(e)[:100]}...")
            raise
            
        finally:
            # Post-inference cleanup
            self._cleanup_after_inference(original_device, model_name)
            self.operation_count += 1
            
            # Periodic maintenance
            if self.operation_count % self.cleanup_interval == 0:
                self._perform_maintenance()
    
    def _record_success(self, device: str, inference_time: float):
        """Record successful operation"""
        stats = self.device_stats[device]
        stats.total_operations += 1
        stats.successful_operations += 1
        
        # Reset consecutive failures on success
        if device == "cuda":
            stats.consecutive_failures = 0
        
        # Update average inference time (exponential moving average)
        alpha = 0.1  # Learning rate for moving average
        if stats.avg_inference_time == 0:
            stats.avg_inference_time = inference_time
        else:
            stats.avg_inference_time = (alpha * inference_time + 
                                       (1 - alpha) * stats.avg_inference_time)
    
    def _record_failure(self, device: str, failure_type: str):
        """Record failed operation"""
        stats = self.device_stats[device]
        stats.total_operations += 1
        stats.failed_operations += 1
        stats.last_failure_time = time.time()
        
        if device == "cuda":
            stats.consecutive_failures += 1
        
        if failure_type in ["out_of_memory", "memory_check_error"]:
            stats.memory_errors += 1
    
    def _cleanup_after_inference(self, device: str, model_name: str):
        """Cleanup memory after inference"""
        if device == "cuda" and self.gpu_available:
            try:
                torch.cuda.empty_cache()
                current_memory = torch.cuda.memory_allocated() / (1024**3)
                logger.debug(f"Post-inference GPU memory: {current_memory:.2f}GB")
                
                # Aggressive cleanup for low-end GPUs
                if self.gpu_info and self.gpu_info.get('is_low_end', False):
                    torch.cuda.synchronize()
                    
            except Exception as e:
                logger.warning(f"GPU cleanup failed: {e}")
        
        # Always run garbage collection for CPU cleanup
        gc.collect()
    
    def _aggressive_gpu_cleanup(self):
        """Perform aggressive GPU memory cleanup"""
        if not self.gpu_available:
            return
            
        try:
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            # Force garbage collection
            collected = gc.collect()
            logger.debug(f"Aggressive cleanup: collected {collected} objects")
        except Exception as e:
            logger.warning(f"Aggressive GPU cleanup failed: {e}")
    
    def _perform_maintenance(self):
        """Periodic maintenance operations"""
        current_time = time.time()
        
        if current_time - self.last_cleanup_time > 60:  # Every minute
            logger.debug("🔧 Performing memory maintenance...")
            
            try:
                # Deep cleanup
                collected = gc.collect()
                
                if self.gpu_available:
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    torch.cuda.reset_peak_memory_stats()
                
                logger.debug(f"Maintenance complete - GC collected {collected} objects")
                
            except Exception as e:
                logger.warning(f"Maintenance failed: {e}")
            
            self.last_cleanup_time = current_time
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        stats = {
            'timestamp': time.time(),
            'operation_count': self.operation_count,
            'forced_cpu_mode': self.forced_cpu_mode,
            'device_stats': {},
            'system_memory': self._get_system_memory_info()
        }
        
        # Add device statistics
        for device, device_stats in self.device_stats.items():
            stats['device_stats'][device] = {
                'total_operations': device_stats.total_operations,
                'success_rate': device_stats.success_rate,
                'avg_inference_time': device_stats.avg_inference_time,
                'memory_errors': device_stats.memory_errors,
                'consecutive_failures': device_stats.consecutive_failures
            }
        
        # Add GPU-specific info
        if self.gpu_available:
            try:
                allocated_gb = torch.cuda.memory_allocated() / (1024**3)
                reserved_gb = torch.cuda.memory_reserved() / (1024**3)
                
                stats['gpu_memory'] = {
                    'allocated_gb': allocated_gb,
                    'reserved_gb': reserved_gb,
                    'max_allocated_gb': torch.cuda.max_memory_allocated() / (1024**3),
                    'limit_gb': self.gpu_memory_limit,
                    'usage_ratio': allocated_gb / self.gpu_memory_limit if self.gpu_memory_limit > 0 else 0
                }
                
                if self.gpu_info:
                    stats['gpu_info'] = self.gpu_info.copy()
                    
            except Exception as e:
                stats['gpu_memory'] = {'error': str(e)}
        
        return stats
    
    def _get_system_memory_info(self) -> Dict[str, Any]:
        """Get system memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percentage': memory.percent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall memory health status"""
        health = {
            'status': 'healthy',
            'warnings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        try:
            # Check system memory
            sys_memory = psutil.virtual_memory()
            health['metrics']['system_memory_usage'] = sys_memory.percent
            
            if sys_memory.percent > 90:
                health['status'] = 'critical'
                health['warnings'].append(f"Critical system memory usage: {sys_memory.percent:.1f}%")
                health['recommendations'].append("Restart application or close other programs")
            elif sys_memory.percent > 80:
                health['status'] = 'warning'
                health['warnings'].append(f"High system memory usage: {sys_memory.percent:.1f}%")
                health['recommendations'].append("Monitor memory usage")
            
            # Check GPU memory and performance
            if self.gpu_available:
                try:
                    allocated_gb = torch.cuda.memory_allocated() / (1024**3)
                    gpu_usage_ratio = allocated_gb / self.gpu_memory_limit if self.gpu_memory_limit > 0 else 0
                    health['metrics']['gpu_memory_usage'] = gpu_usage_ratio * 100
                    
                    if gpu_usage_ratio > 0.9:
                        health['status'] = 'critical'
                        health['warnings'].append(f"Critical GPU memory usage: {gpu_usage_ratio:.1%}")
                        health['recommendations'].append("Force CPU mode or restart application")
                    elif gpu_usage_ratio > 0.8:
                        if health['status'] == 'healthy':
                            health['status'] = 'warning'
                        health['warnings'].append(f"High GPU memory usage: {gpu_usage_ratio:.1%}")
                        health['recommendations'].append("Consider reducing batch size")
                        
                except Exception as e:
                    health['warnings'].append(f"GPU health check failed: {e}")
            
            # Check device performance
            cuda_stats = self.device_stats["cuda"]
            if cuda_stats.total_operations > 5:
                success_rate = cuda_stats.success_rate
                health['metrics']['gpu_success_rate'] = success_rate * 100
                
                if success_rate < 0.5:
                    health['status'] = 'critical'
                    health['warnings'].append(f"Low GPU success rate: {success_rate:.1%}")
                    health['recommendations'].append("Consider forcing CPU-only mode")
                elif success_rate < 0.8:
                    if health['status'] == 'healthy':
                        health['status'] = 'warning'
                    health['warnings'].append(f"Moderate GPU success rate: {success_rate:.1%}")
                    health['recommendations'].append("Monitor GPU stability")
            
            # Check for forced CPU mode
            if self.forced_cpu_mode:
                health['warnings'].append("Currently in forced CPU mode")
                remaining = max(0, self.forced_cpu_until - time.time())
                if remaining > 0:
                    health['recommendations'].append(f"GPU will be re-enabled in {remaining:.0f}s")
            
        except Exception as e:
            health['status'] = 'error'
            health['warnings'].append(f"Health check failed: {e}")
        
        return health
    
    def force_cpu_mode(self, duration_seconds: int = 300):
        """Force CPU-only mode for specified duration"""
        logger.info(f"🚫 Forcing CPU-only mode for {duration_seconds}s")
        self.forced_cpu_mode = True
        self.forced_cpu_until = time.time() + duration_seconds
        
        # Aggressive cleanup when forcing CPU mode
        self._aggressive_gpu_cleanup()
    
    def reset_gpu_failures(self):
        """Reset GPU failure count to re-enable GPU usage"""
        logger.info("🔄 Resetting GPU failure count")
        self.device_stats["cuda"].reset_failures()
        self.forced_cpu_mode = False
        self.forced_cpu_until = 0.0
        
        # Clear GPU memory
        if self.gpu_available:
            self._aggressive_gpu_cleanup()
    
    def print_status(self):
        """Print current status summary"""
        stats = self.get_memory_stats()
        health = self.get_health_status()
        
        print(f"\n{'='*50}")
        print(f"GPU Memory Manager Status")
        print(f"{'='*50}")
        print(f"Operations completed: {stats['operation_count']}")
        print(f"Health status: {health['status'].upper()}")
        
        if self.gpu_available:
            gpu_stats = stats['device_stats']['cuda']
            gpu_mem = stats.get('gpu_memory', {})
            print(f"GPU: {self.gpu_info['name']}")
            print(f"GPU Success Rate: {gpu_stats['success_rate']:.1%}")
            print(f"GPU Memory: {gpu_mem.get('allocated_gb', 0):.2f}GB / {self.gpu_memory_limit:.2f}GB")
        
        cpu_stats = stats['device_stats']['cpu']
        sys_mem = stats['system_memory']
        print(f"CPU Success Rate: {cpu_stats['success_rate']:.1%}")
        print(f"System Memory: {sys_mem.get('percentage', 0):.1f}%")
        
        if health['warnings']:
            print(f"\nWarnings:")
            for warning in health['warnings']:
                print(f"  ⚠️  {warning}")
        
        if health['recommendations']:
            print(f"\nRecommendations:")
            for rec in health['recommendations']:
                print(f"  💡 {rec}")
        
        print(f"{'='*50}\n")


def optimize_torch_for_low_end_gpu():
    """Apply PyTorch optimizations for low-end GPUs like GT 710"""
    try:
        # Limit CPU threads to prevent resource contention
        available_cores = psutil.cpu_count(logical=False) or 2
        torch.set_num_threads(min(4, available_cores))
        
        # Disable gradient computation globally for inference
        torch.set_grad_enabled(False)
        
        if torch.cuda.is_available():
            # Enable optimizations for consistent input sizes
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.enabled = True
            
            # Enable mixed precision if supported
            if hasattr(torch.backends.cuda.matmul, 'allow_tf32'):
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
            
            # Optimize memory allocation
            torch.cuda.empty_cache()
            
        logger.info("🎮 PyTorch optimizations for low-end GPU applied")
        
    except Exception as e:
        logger.warning(f"Failed to apply low-end GPU optimizations: {e}")


# Global memory manager instance
gpu_memory_manager = None

def get_memory_manager(**kwargs) -> HybridGPUMemoryManager:
    """Get or create the global memory manager instance"""
    global gpu_memory_manager
    if gpu_memory_manager is None:
        gpu_memory_manager = HybridGPUMemoryManager(**kwargs)
        optimize_torch_for_low_end_gpu()
    return gpu_memory_manager


# Convenience functions for backward compatibility
@contextmanager
def managed_inference(model_name: str = "Unknown", 
                     model_type: str = "default",
                     estimated_memory_mb: Optional[float] = None):
    """Convenience wrapper for the global memory manager"""
    manager = get_memory_manager()
    with manager.managed_inference(model_name, model_type, estimated_memory_mb) as device:
        yield device


def get_optimal_device(model_type: str = "default", 
                      estimated_memory_mb: Optional[float] = None) -> str:
    """Get optimal device for inference"""
    manager = get_memory_manager()
    return manager.get_optimal_device(model_type, estimated_memory_mb)


def get_memory_stats() -> Dict[str, Any]:
    """Get memory statistics"""
    manager = get_memory_manager()
    return manager.get_memory_stats()


def get_health_status() -> Dict[str, Any]:
    """Get memory health status"""
    manager = get_memory_manager()
    return manager.get_health_status()


def force_cpu_mode(duration_seconds: int = 300):
    """Force CPU-only mode for specified duration"""
    manager = get_memory_manager()
    manager.force_cpu_mode(duration_seconds)


def reset_gpu_failures():
    """Reset GPU failure count to re-enable GPU usage"""
    manager = get_memory_manager()
    manager.reset_gpu_failures()


def print_status():
    """Print current status summary"""
    manager = get_memory_manager()
    manager.print_status()


# Example usage
if __name__ == "__main__":
    # Initialize the memory manager
    manager = get_memory_manager()
    
    # Example inference
    with managed_inference("YOLOv5", "yolo") as device:
        print(f"Running inference on {device}")
        # Your model inference code here
        time.sleep(0.1)  # Simulated inference
    
    # Print status
    print_status()