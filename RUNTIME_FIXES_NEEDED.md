# MISSING PACKAGES FOUND DURING RUNTIME TESTING
# Add these to requirements.txt for final rebuild

## CRITICAL - Required by transformers + TensorFlow 2.x
tf-keras>=2.17.0  # Backwards-compatible Keras for TensorFlow 2.x + transformers

## Already in requirements but verify:
python-dotenv>=1.0.0  # Already present ✓

# NOTES:
# - tf-keras is required because transformers doesn't support Keras 3 yet
# - Without tf-keras, web service crashes on startup with:
#   "ValueError: Your currently installed version of Keras is Keras 3, but this is not yet supported in Transformers"

# REBUILD NEEDED: Yes
# After adding tf-keras to requirements.txt, rebuild web image:
# docker-compose build --no-cache web
