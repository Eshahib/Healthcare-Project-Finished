# NeuralSeek Integration Setup Guide

## Overview
This guide will help you connect your symptom checker backend to your NeuralSeek API.

## Step 1: Get Your NeuralSeek API Credentials

1. Log into your NeuralSeek account
2. Navigate to API Settings or Developer Console
3. Get the following:
   - **API Key** (or Bearer Token)
   - **API URL** (endpoint for your NeuralSeek API)
   - **Project ID** (if applicable)

## Step 2: Configure Environment Variables

Add these to your `.env` file in the `Back_End` directory:

```bash
# NeuralSeek API Configuration
NEURALSEEK_API_URL=https://api.neuralseek.com/v1/seek
NEURALSEEK_API_KEY=your_api_key_here
NEURALSEEK_PROJECT_ID=your_project_id_here
```

### Finding Your NeuralSeek API Details:

1. **API URL**: Check your NeuralSeek dashboard for the API endpoint
   - Common formats:
     - `https://api.neuralseek.com/v1/seek`
     - `https://your-instance.neuralseek.com/api/v1/seek`
     - Check your NeuralSeek documentation for the exact endpoint

2. **API Key**: 
   - Usually found in API Settings or Developer Console
   - May be called "API Key", "Bearer Token", or "Access Token"

3. **Project ID** (optional):
   - Some NeuralSeek instances require a project ID
   - Leave empty if not required

## Step 3: Update NeuralSeek API Integration

The integration module (`neuralseek.py`) may need customization based on your specific NeuralSeek API structure. 

### Common API Structures:

#### Option 1: Standard REST API
```python
# In neuralseek.py, the current implementation assumes:
POST /api/seek
Headers: Authorization: Bearer {API_KEY}
Body: {
    "query": "your prompt",
    "project_id": "optional",
    "max_tokens": 1000
}
Response: {
    "response": "LLM response text",
    # or "answer", "text" depending on your API
}
```

#### Option 2: Different Endpoint Structure
If your NeuralSeek API uses a different structure, update the `analyze_symptoms_with_neuralseek` function in `neuralseek.py`:

```python
# Example for different API structure
payload = {
    "question": prompt,
    "context": comments,
    "response_format": "structured"
}

headers = {
    "X-API-Key": NEURALSEEK_API_KEY,  # If using X-API-Key instead of Bearer
    "Content-Type": "application/json"
}
```

## Step 4: Test the Integration

1. **Install the requests library** (if not already installed):
```bash
cd Back_End
source venv_mac/bin/activate
pip install requests
```

2. **Test the API connection**:
```bash
# Test creating a symptom entry (this will trigger NeuralSeek analysis)
curl -X POST http://localhost:8000/api/symptoms \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["Fever", "Cough"],
    "comments": "Started yesterday"
  }'
```

3. **Check the backend logs** for NeuralSeek API calls:
   - Look for "Analyzing symptoms for entry X with NeuralSeek..."
   - Check for any error messages

## Step 5: Customize the Prompt (Optional)

You can customize the prompt sent to NeuralSeek by editing the `analyze_symptoms_with_neuralseek` function in `neuralseek.py`:

```python
prompt = f"""Your custom prompt here:

Symptoms: {symptoms_text}
Additional Information: {comments}

Your instructions to the LLM...
"""
```

## Troubleshooting

### Error: "NEURALSEEK_API_KEY not set"
- Make sure you've added `NEURALSEEK_API_KEY` to your `.env` file
- Restart the backend server after updating `.env`

### Error: "NeuralSeek API request failed"
- Check that your API URL is correct
- Verify your API key is valid
- Check if your NeuralSeek API requires different authentication (e.g., X-API-Key instead of Bearer)
- Verify your API endpoint accepts POST requests

### Error: "No response text received"
- Check the response structure from your NeuralSeek API
- Update the response parsing in `neuralseek.py`:
  ```python
  # Try different response keys
  analysis_text = result.get("response") or result.get("answer") or result.get("text") or result.get("content")
  ```

### API Response Structure Different
If your NeuralSeek API returns a different structure, update the parsing in `analyze_symptoms_with_neuralseek`:

```python
# Example: If your API returns structured data
if "data" in result:
    analysis_text = result["data"]["response"]
elif "result" in result:
    analysis_text = result["result"]
else:
    analysis_text = str(result)  # Fallback
```

## API Endpoints

After setup, you can use these endpoints:

1. **Create Symptom Entry** (auto-analyzes with NeuralSeek):
   ```
   POST /api/symptoms
   ```
   - Creates symptom entry
   - Automatically triggers NeuralSeek analysis in background

2. **Manually Trigger Analysis**:
   ```
   POST /api/symptoms/{symptom_id}/analyze
   ```
   - Manually trigger NeuralSeek analysis for a symptom entry

3. **Get Symptom Entry with Diagnosis**:
   ```
   GET /api/symptoms/{symptom_id}
   ```
   - Returns symptom entry with diagnosis (if available)

## Next Steps

1. ✅ Add your NeuralSeek API credentials to `.env`
2. ✅ Customize the API integration if needed
3. ✅ Test the integration
4. ✅ Update the frontend to display diagnosis results
5. ✅ Add error handling and user feedback

## Support

If you need help:
1. Check your NeuralSeek API documentation
2. Review the error messages in backend logs
3. Test your NeuralSeek API directly with curl or Postman
4. Update `neuralseek.py` to match your API structure

