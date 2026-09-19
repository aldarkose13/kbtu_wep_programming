# Current code is a basic demo for a docker app

In the Dockerfile default port is 8000, so if you have something running on that port disable it

1. Clone the project
2. Open terminal
3. Run `docker build -t kbtu_web_project .`
4. Run `docker run -p 8000:8000 -d --name edil-elkhan-container kbtu_web_project`
5. Open http://localhost:8000

As a result, you will have a web app running on port 8000, and it will say "message": "Hello, World!"