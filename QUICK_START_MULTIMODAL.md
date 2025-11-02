# ⚡ Quick Start: Multi-Modal Product Search

**Time to deploy**: 5 minutes  
**Prerequisites**: Docker, Docker Compose

---

## 🚀 Step 1: Start All Services (1 minute)

```powershell
# Start Docker containers
docker-compose -f docker-compose.secure.yml up -d

# Wait for startup (check logs)
docker logs test_model-web-1 --tail 20
```

**Expected**: All containers running, no errors in logs

---

## 🔧 Step 2: Start Background Workers (1 minute)

**Open new terminal** and run:

```powershell
# Start all workers together
docker exec -it test_model-web-1 python -m app.workers.manager
```

**Expected logs**:
```
✅ scraper-worker-1 initialized
✅ image-ai-worker-1 initialized
🚀 scraper-worker-1 starting...
🚀 image-ai-worker-1 starting...
✅ CLIP model loaded
✅ Image processor loaded
```

**Keep this terminal open!** Workers must run continuously.

---

## 🧪 Step 3: Test the Integration (3 minutes)

### Test 1: Text Search (Baseline)

```powershell
curl -X POST "http://localhost:8000/api/v1/comparison/smart-search?query=iPhone%2015&sites=amazon&max_results=5"
```

**Expected**: JSON with product results

### Test 2: Barcode Search

```powershell
curl -X POST "http://localhost:8000/api/v1/comparison/search-by-barcode?barcode=049000050103&sites=amazon"
```

**Expected**: Products matching barcode

### Test 3: Image Search

**First, get a test image:**
1. Take photo of any product (phone, book, cereal box)
2. Save as `test_product_image.jpg` in project root

**Then test:**
```powershell
# Run automated test
python test_multimodal_search.py
```

**Expected output**:
```
🧪 TEST: Image Search
✅ Search Status: success
🔍 Detected Query: [product name]
🛒 Found [X] products
✅ IMAGE SEARCH TEST PASSED!
```

---

## ✅ Success Checklist

- [ ] All Docker containers running (`docker ps`)
- [ ] Workers started and showing "starting..." message
- [ ] Text search returns products
- [ ] Barcode search returns products
- [ ] Image search returns products (if test image provided)
- [ ] No errors in worker logs

---

## 🎯 What You Can Do Now

### **Upload an Image → Get Prices**

```bash
curl -X POST http://localhost:8000/api/v1/comparison/search-by-image \
  -F "file=@my_product.jpg" \
  -F "sites=amazon,walmart,ebay"
```

### **Scan a Barcode → Get Prices**

```bash
curl -X POST "http://localhost:8000/api/v1/comparison/search-by-barcode?barcode=YOUR_BARCODE&sites=amazon,walmart"
```

### **Search by Text → Get Prices**

```bash
curl -X POST "http://localhost:8000/api/v1/comparison/smart-search?query=MacBook%20Pro&sites=amazon,ebay"
```

---

## 📊 How It Works

```
User uploads image → Image AI Worker detects product → Scraper Worker searches → Returns live prices
     (instant)              (~2 seconds)                    (~5 seconds)            (<8 seconds total)
```

---

## 🐛 Common Issues

### Workers Not Starting?

**Check Redis connection:**
```powershell
docker exec -it test_model-redis-1 redis-cli ping
```

**Expected**: `PONG`

### No Products Found?

**Check scraper service:**
```powershell
curl -X POST http://localhost:3001/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"iPhone","sites":["amazon"]}'
```

**Expected**: Products array with results

### Image Detection Not Working?

**Check CLIP model loaded:**
```powershell
docker logs test_model-web-1 | grep "CLIP"
```

**Expected**: "✅ CLIP service ready"

---

## 📚 Full Documentation

- **Architecture**: `MULTIMODAL_SEARCH_COMPLETE.md`
- **Deployment**: `DEPLOYMENT_CHECKLIST.md`
- **Testing**: Run `python test_multimodal_search.py`

---

## 🎉 Next Steps

1. **Test with your own images** - Upload photos of products you want to price-compare
2. **Monitor the workers** - Watch logs to see events being processed
3. **Check the database** - See products being saved in real-time
4. **Build the UI** - Connect frontend to these endpoints

---

**Status**: ✅ Ready to use!  
**Total time**: ~5 minutes to full deployment
