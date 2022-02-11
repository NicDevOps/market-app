# market-app


# Welcome to my market trade platform github project
### This platform is use to study the market flow by the use of candlestick graph with javascript
### and will scan all market for candlestick pattern recognition !



```
nc -zv test-nginx 8080
curl http://test-nginx:8080
python3 -m venv .venv
source .venv/bin/activate
docker build -t nicdevops/market-app .
docker run --rm -p 5000:5000 nicdevops/market-app
http://127.0.0.1:5000/login
kubectl exec -it market-app-9c56f549d-qkdzd -- bash
kubectl patch pv pvc-4a836b58-49ed-41e7-b33e-8e9194893aa1 --type json -p '[{"op": "remove", "path": "/spec/claimRef"}]'
```