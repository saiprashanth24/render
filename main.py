from fastapi import FastAPI, Request
import logging
import urllib.parse
import urllib.request
import json

app = FastAPI()

# Setup logging
logger = logging.getLogger("zoho_search")
logging.basicConfig(level=logging.INFO)

@app.post("/zoho_search_query")
async def zoho_search_query(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "")
        service_name = body.get("service_name", "")
        no_of_results = int(body.get("no_of_results", 3))

        logger.info(f"🔍 QUERY RECEIVED: '{query}' | SERVICE: '{service_name}' | RESULTS: {no_of_results}")

        # URL encode query
        encoded_query = urllib.parse.quote_plus(query)
        base_url = "https://search.zoho.com/websearch"
        params = {
            "lang": "en",
            "site_region": "global", 
            "type": "4",
            "stream": "true",
            "no_of_results": str(min(no_of_results, 10)),
            "query": encoded_query,
            "version_id": "5"
        }
        if service_name:
            params["service_name"] = service_name
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{query_string}"

        logger.info(f"🌐 API REQUEST: {full_url}")

        request_obj = urllib.request.Request(full_url)
        request_obj.add_header('Accept', 'text/event-stream')

        summary_parts = []
        search_results = []

        with urllib.request.urlopen(request_obj) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        if 'summary' in data:
                            summary_parts.append(data['summary'])
                        elif 'results' in data:
                            search_results = data['results']
                    except json.JSONDecodeError:
                        continue

        full_summary = ''.join(summary_parts)
        response_data = {
            "query": query,
            "service_name": service_name,
            "summary": full_summary,
            "results": search_results,
            "total_results": len(search_results),
            "status": "success"
        }

        logger.info(f"✅ RESPONSE SUCCESS: Query='{query}' | Results={len(search_results)}")
        return response_data

    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        return {
            "query": body.get("query", ""),
            "service_name": body.get("service_name", ""),
            "summary": "",
            "results": [],
            "total_results": 0,
            "status": "error",
            "error": str(e)
        }
