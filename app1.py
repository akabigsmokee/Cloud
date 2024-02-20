from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import json
import subprocess
import random
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Load user credentials from JSON file
with open('users.json') as f:
    users = json.load(f)

container_counter = 8

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if 'username' in session:  # Check if the user is already logged in
        username = session['username']
        return render_template('dashboard.html', username=username)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the provided credentials match the ones in the JSON file
        if username in users and password == users[username]:
            session['username'] = username  # Store the username in the session
            return render_template('dashboard.html', username=username)
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('dashboard.html')

@app.route('/create_container', methods=['POST'])
def create_container():
    if 'username' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))

    username = session['username']
    global container_counter
    container_name = request.form['container_name']
    ssh_username = request.form['ssh_username']
    ssh_password = request.form['ssh_password']

    # Increment the container counter
    container_counter += 1

    # Generate a random host port number based on the container counter
    host_port = random.randint(10000, 20000) + container_counter

    # Build the Docker image with the provided SSH password argument
    image_name = f'image-{username}-{container_counter}'
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
            return render_template('dashboard.html', username=session['username'], container_info=container_info)
        else:
            return render_template('dashboard.html', username=session['username'], error_message='Container deployment failed')
    else:
        # Error occurred during container deployment
        error_message = error.decode().strip()
        return render_template('dashboard.html', username=session['username'], error_message=error_message)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()  # Clear the session
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route('/my_containers')
def my_containers():
    if 'username' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))

    username = session['username']

    # Execute Docker command to get container details
    ps_command = 'docker ps -a --format "ID: {{.ID}} Name: {{.Names}} Image: {{.Image}}  Status: {{.Status}} Ports: {{.Ports}}"'
    ps_output = subprocess.check_output(ps_command, shell=True).decode().strip()

    containers = []
    for line in ps_output.split('\n'):
        container_info = line.split()
        if len(container_info) >= 4:
            container_id = container_info[1]
            container_name = container_info[3]
            image_name = container_info[5]
            ports_info = container_info[11]
            status = container_info[7]
            is_running = container_info[7] == 'Up'
            is_stopped = container_info[7] == 'Exited'

            # Extract the published port from the ports information
            published_port = None
            if '->' in ports_info:
                published_port = ports_info.split('->')[0].split(':')[-1]
                if ':' in published_port:
                    published_port = published_port.split(':')[-1]

            if image_name.startswith(f'image-{username}-'):
              containers.append({
                'container_id': container_id,
                'container_name': container_name,
                'image_name': image_name,
                'published_port': published_port,
		'status': status,
		'is_running': is_running,
                'is_stopped': is_stopped
               })

    return render_template('my_containers.html', username=username, containers=containers)

@app.route('/stop_container', methods=['POST'])
def stop_container():
    if 'username' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))

    container_id = request.form['container_id']

    # Execute Docker command to stop the container
    stop_command = f'docker stop {container_id}'
    subprocess.run(stop_command, shell=True)

    return redirect(url_for('my_containers'))

@app.route('/delete_container', methods=['POST'])
def delete_container():
    if 'username' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))

    container_id = request.form['container_id']
    image_name = request.form['image_name']

    # Execute Docker command to stop and delete the container
    stop_command = f'docker stop {container_id}'
    subprocess.run(stop_command, shell=True)

    delete_command = f'docker rm {container_id}'
    subprocess.run(delete_command, shell=True)

    # Execute Docker command to delete the associated image
    delete_image_command = f'docker rmi {image_name}'
    subprocess.run(delete_image_command, shell=True)

    return redirect(url_for('my_containers'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

