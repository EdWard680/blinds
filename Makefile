# Commands
DOCKER_TEMPLATE_COMPILER=dockerfile-template
DOCKERFILE_TEMPLATE=Dockerfile.template

# Device used for local testing
BALENA_MACHINE_NAME=raspberrypi3
BLINDS_APP_NAME=blinds-controller

# Device name of blinds controller
BLINDS_ADDRESS=pi-3d-land.local

Dockerfile: $(DOCKERFILE_TEMPLATE)
	$(DOCKER_TEMPLATE_COMPILER) -f $< -d BALENA_MACHINE_NAME=$(BALENA_MACHINE_NAME) > $@

local-test: Dockerfile
	sudo balena local push $(BLINDS_ADDRESS) -n $(BLINDS_APP_NAME)
