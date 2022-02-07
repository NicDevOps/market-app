# market-app

```
nc -zv test-nginx 8080
curl http://test-nginx:8080
python3 -m venv .venv
source .venv/bin/activate
docker build -t nicdevops/market-app .
docker run --rm -p 5000:5000 nicdevops/market-app
http://127.0.0.1:5000/login
kubectl exec -it market-app-9c56f549d-qkdzd -- bash
```