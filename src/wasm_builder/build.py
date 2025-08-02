import docker
import os
import logging
import yaml
import time
from ..colors import Colors

def build_project(project_dir, reg_user, reg_pass, detached, metrics, metrics_enabled):
    
    build_metrics = {}
    start_time = 0
    
    # Check if the project directory is valid
    if not os.path.exists(f"{project_dir}/gen"):
        logging.error(f"{Colors.RED}Project directory is not valid{Colors.RESET}")
        return
    
    print(f'{Colors.BLUE}Building WASM components{Colors.RESET}')
    
    os.environ["DOCKER_CLIENT_TIMEOUT"] = "120"
    os.environ["DOCKER_TIMEOUT"] = "120"
    
    # Docker client
    client = docker.from_env()
    
    if metrics_enabled:
        start_time = time.time()
    
    # Build the images for the project if they don't exist
    try:
        client.images.get("wash-build-image:latest")
    except docker.errors.ImageNotFound:
        
        print(f'{Colors.YELLOW} - Building wash-build-image from Dockerfile...{Colors.RESET}')
        client.images.build(
            path="src/wasm_builder/docker",
            dockerfile="build.Dockerfile",
            tag="wash-build-image:latest"
        )
        if metrics_enabled:
            build_metrics['image_build_time'] = '%.3f'%(time.time() - start_time)
        
    try:
        wait_list = []
        
        for task in os.listdir(f"{project_dir}/gen"):
            __build_wasm(f"{project_dir}/gen/{task}", client, reg_user, reg_pass, detached, wait_list)
            
        if detached == 'True':
            
            print(f'{Colors.BLUE}Waiting for build to finish...{Colors.RESET}')
            for container_name in wait_list:
                try:
                    container = client.containers.get(container_name)
                    result = container.wait()
                    exit_code = result['StatusCode']
                    
                    if exit_code == 0:
                        print(f"{Colors.GREEN} - Build successful for {container_name}, removing container{Colors.RESET}")
                        container.remove()
                    else:
                        print(f"{Colors.RED} - Build failed for {container_name} (exit code: {exit_code}), keeping container for debugging{Colors.RESET}")
                        
                except Exception as e:
                    print(f"{Colors.YELLOW} - Error waiting for container {container_name}: {e}{Colors.RESET}")
                    continue
        
    except Exception as e:
        logging.error(f"{Colors.RED}Error building project: {e}{Colors.RESET}")
        return
    
    if metrics_enabled:
        build_metrics['components_build_time'] = '%.3f'%(time.time() - start_time)
        metrics['build'] = build_metrics
        
    print(f"{Colors.GREEN}Project built successfully{Colors.RESET}")
    
def __build_wasm(task_dir, client, reg_user, reg_pass, detached, wait_list):
    
    wadm = __parse_yaml(f"{task_dir}/wadm.yaml")
    
    path = os.path.abspath(task_dir)
    
    oci_url = wadm['spec']['components'][0]['properties']['image']
    name = wadm['spec']['components'][0]['name'] + '-build'
    
    # Check if container with the same name already exists and remove it
    try:
        existing_container = client.containers.get(name)
        print(f"{Colors.YELLOW} - Removing existing container {name}{Colors.RESET}")
        existing_container.remove(force=True)
    except docker.errors.NotFound:
        # Container doesn't exist, continue
        pass
    except Exception as e:
        print(f"{Colors.RED} - Warning: Could not remove existing container {name}: {e}{Colors.RESET}")
    
    uid = os.getuid()
    gid = os.getgid()
    
    # Build the wasm module
    print(f"{Colors.BLUE} - Building WASM module {oci_url}{Colors.RESET}")
    container = client.containers.run(
        "wash-build-image:latest",
        environment=[f'REGISTRY={oci_url}',
                     f'WASH_REG_USER={reg_user}',
                     f'WASH_REG_PASSWORD={reg_pass}',
                     f'HOST_UID={uid}',
                     f'HOST_GID={gid}'],
        volumes={path: {'bind': '/app', 'mode': 'rw'}},
        remove=False,
        detach=True,
        name=name
    )
    
    if detached == 'False':
        container.wait()
    else:
        wait_list.append(name)
    

def __parse_yaml(yaml_file):
    with open(yaml_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None