# Commands
DOCKER_TEMPLATE_COMPILER=dockerfile-template
DOCKERFILE_TEMPLATE=Dockerfile.template

# Device used for local testing
BALENA_MACHINE_NAME=raspberrypi3

Dockerfile: $(DOCKERFILE_TEMPLATE)
	$(DOCKER_TEMPLATE_COMPILER) -f $< -d BALENA_MACHINE_NAME=$(BALENA_MACHINE_NAME) > $@

