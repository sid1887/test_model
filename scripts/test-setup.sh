#!/bin/bash
# filepath: d:\dev_packages\test_model\scripts\test-setup.sh

# Integration test script to verify the Make + Docker-Compose Profiles setup (Bash version)
# This script provides basic validation of the development environment setup.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
TEST_RESULTS=()
START_TIME=$(date +%s)
SKIP_SERVICE_TEST=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-service-test)
            SKIP_SERVICE_TEST=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--skip-service-test] [--verbose]"
            echo "  --skip-service-test  Skip the actual service startup test"
            echo "  --verbose           Enable verbose output"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
write_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$(date): $1" >&2
    fi
}

write_success() {
    echo -e "${GREEN}✅ $1${NC}"
    TEST_RESULTS+=("PASS: $1")
}

write_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    TEST_RESULTS+=("WARN: $1")
}

write_error() {
    echo -e "${RED}❌ $1${NC}"
    TEST_RESULTS+=("FAIL: $1")
}

write_test_header() {
    echo ""
    echo -e "${CYAN}🔍 $1${NC}"
    echo -e "${CYAN}$(printf '=%.0s' $(seq 1 $((${#1} + 3))))${NC}"
}

# Test prerequisites
test_prerequisites() {
    write_test_header "Prerequisites"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        write_success "Docker is available"
    else
        write_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        write_success "Docker Compose is available"
    else
        write_error "Docker Compose is not installed or not in PATH"
        return 1
    fi
    
    # Check Make
    if command -v make &> /dev/null; then
        write_success "Make is available"
    else
        write_error "Make is not installed or not in PATH"
        write_warning "You can install make via: sudo apt-get install build-essential (Ubuntu/Debian)"
        return 1
    fi
    
    return 0
}

# Test Docker Compose profiles
test_profiles() {
    write_test_header "Docker Compose Profiles"
    
    local profiles=("core" "worker" "scraper" "monitor")
    local all_profiles_valid=true
    
    for profile in "${profiles[@]}"; do
        write_info "Validating '$profile' profile configuration..."
        if docker-compose --profile "$profile" config > /dev/null 2>&1; then
            write_success "$profile profile configuration is valid"
        else
            write_error "$profile profile configuration failed"
            all_profiles_valid=false
        fi
    done
    
    # Test multiple profiles combination
    write_info "Testing multiple profiles combination..."
    local combined_profiles=""
    for profile in "${profiles[@]}"; do
        combined_profiles="$combined_profiles --profile $profile"
    done
    
    if docker-compose $combined_profiles config > /dev/null 2>&1; then
        write_success "Multiple profiles configuration is valid"
    else
        write_error "Multiple profiles configuration failed"
        all_profiles_valid=false
    fi
    
    return $all_profiles_valid
}

# Test Make commands
test_make_commands() {
    write_test_header "Make Commands"
    
    # Test help
    if make help > /dev/null 2>&1; then
        write_success "make help works"
    else
        write_error "make help failed"
        return 1
    fi
    
    # Test that Makefile exists and has required targets
    if [[ ! -f "Makefile" ]]; then
        write_error "Makefile not found"
        return 1
    fi
    
    local required_targets=("start" "stop" "logs" "start-minimal" "start-no-scraper" "status" "clean")
    local all_targets_exist=true
    
    for target in "${required_targets[@]}"; do
        if grep -q "^$target:" Makefile; then
            write_success "make $target target exists"
        else
            write_error "make $target target not found"
            all_targets_exist=false
        fi
    done
    
    return $all_targets_exist
}

# Test shell scripts
test_shell_scripts() {
    write_test_header "Shell Scripts"
    
    if [[ -f "scripts/start-all.sh" ]]; then
        write_success "start-all.sh exists"
        
        # Check if script has proper shebang
        if head -1 "scripts/start-all.sh" | grep -q "#!/bin/bash"; then
            write_success "start-all.sh has proper shebang"
        else
            write_warning "start-all.sh may be missing shebang"
        fi
        
        # Check if script is executable
        if [[ -x "scripts/start-all.sh" ]]; then
            write_success "start-all.sh is executable"
        else
            write_warning "start-all.sh is not executable (may need chmod +x)"
        fi
    else
        write_warning "start-all.sh not found"
    fi
    
    if [[ -f "scripts/start-all.ps1" ]]; then
        write_success "start-all.ps1 exists"
    else
        write_warning "start-all.ps1 not found"
    fi
    
    return 0
}

# Generate test report
write_test_report() {
    write_test_header "Test Report Summary"
    
    local total_tests=${#TEST_RESULTS[@]}
    local passed_tests=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^PASS:" || true)
    local failed_tests=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^FAIL:" || true)
    local warning_tests=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^WARN:" || true)
    
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo ""
    echo -e "${CYAN}📊 Test Execution Summary${NC}"
    echo -e "${CYAN}=========================${NC}"
    echo "Total Tests: $total_tests"
    echo -e "${GREEN}Passed: $passed_tests${NC}"
    echo -e "${RED}Failed: $failed_tests${NC}"
    echo -e "${YELLOW}Warnings: $warning_tests${NC}"
    echo "Duration: ${duration} seconds"
    echo ""
    
    if [[ $failed_tests -gt 0 ]]; then
        echo -e "${RED}❌ Failed Tests:${NC}"
        printf '%s\n' "${TEST_RESULTS[@]}" | grep "^FAIL:" | sed 's/^FAIL: /  - /'
        echo ""
    fi
    
    if [[ $warning_tests -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Warnings:${NC}"
        printf '%s\n' "${TEST_RESULTS[@]}" | grep "^WARN:" | sed 's/^WARN: /  - /'
        echo ""
    fi
    
    # Success rate
    local success_rate=0
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$((passed_tests * 100 / total_tests))
    fi
    
    if [[ $success_rate -ge 90 ]]; then
        echo -e "${GREEN}🎉 Success Rate: ${success_rate}% - Excellent!${NC}"
    elif [[ $success_rate -ge 70 ]]; then
        echo -e "${YELLOW}👍 Success Rate: ${success_rate}% - Good${NC}"
    else
        echo -e "${RED}⚠️  Success Rate: ${success_rate}% - Needs Attention${NC}"
    fi
    
    return $((failed_tests == 0))
}

# Main execution
main() {
    write_info "🚀 Starting Make + Docker-Compose Profiles Integration Test (Bash)"
    echo ""
    
    # Check prerequisites
    if ! test_prerequisites; then
        write_error "Prerequisites check failed"
        write_test_report
        exit 1
    fi
    
    echo ""
    
    # Run tests
    local all_tests_passed=true
    
    if ! test_shell_scripts; then
        all_tests_passed=false
    fi
    echo ""
    
    if ! test_make_commands; then
        all_tests_passed=false
    fi
    echo ""
    
    if ! test_profiles; then
        all_tests_passed=false
    fi
    echo ""
    
    # Generate comprehensive test report
    if write_test_report && [[ "$all_tests_passed" == "true" ]]; then
        write_success "🎉 All tests passed! Your Make + Docker-Compose Profiles setup is working correctly."
        echo ""
        write_info "💡 To test the full system:"
        echo "   make start-minimal  # Test core services"
        echo "   make start          # Test all services"
        echo "   make stop           # Clean up"
        echo ""
        write_info "💡 Available profiles for testing:"
        echo "   --profile core      # Essential services (postgres, redis, web)"
        echo "   --profile worker    # Background processing (celery, flower)"
        echo "   --profile scraper   # Data collection service"
        echo "   --profile monitor   # Monitoring stack (prometheus, grafana)"
        exit 0
    else
        write_error "Some tests failed. Please check the configuration."
        exit 1
    fi
}

# Run main function
main "$@"
