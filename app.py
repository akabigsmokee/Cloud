from flask import Flask, render_template, request, redirect, url_for
import json
import subprocess
import random

app = Flask(__name__)

# Load user credentials from JSON file
with open('users.json') as f:
    users = json.load(f)

container_counter = 4

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the provided credentials match the ones in the JSON file
        if username in users and password == users[username]:
            return render_template('dashboard.html', username=username)
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('dashboard.html')

@app.route('/create_container', methods=['POST'])
def create_container():
    global container_counter

    container_name = request.form['container_name']
    ssh_username = request.form['ssh_username']
    ssh_password = request.form['ssh_password']

    # Increment the container counter
    container_counter += 1

    # Generate a random host port number based on the container counter
    host_port = random.randint(10000, 20000) + container_counter

    # Build the Docker image with the provided SSH password argument
    image_name = f'image-{container_counter}'
    subprocess.run(f'docker build -t {image_name} --build-arg PASSWORD={ssh_password} .', shell=True)

    # Execute Docker command to create a container using the custom image
    command = f'docker run -d --name {container_name} -p {host_port}:22 {image_name}'
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode == 0:
        # Container deployed successfully

        # Check if the container exists in the output of `docker ps -a` command
        ps_command = 'docker ps -a'
        ps_output = subprocess.check_output(ps_command, shell=True).decode().strip()

        if container_name in ps_output:
            container_info = f'Container deployed successfully! You may access it with ssh root@192.168.255.150 -p {host_port}'
            return render_template('dashboard.html', username=request.form.get('username'), container_info=container_info)
        else:
            return render_template('dashboard.html', username=request.form.get('username'), error_message='Container deployment failed')
    else:
        # Error occurred during container deployment
        error_message = error.decode().strip()
        return render_template('dashboard.html', username=request.form.get('username'), error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
