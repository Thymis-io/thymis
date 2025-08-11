# Your Project in Thymis

Thymis is designed to be extensible, allowing you to integrate your own projects and software into the Thymis ecosystem. This section shows you [how to set up external repositories](./external-projects/external-repositories.md), [access the Thymis project git repository](./external-projects/git-repository.md), [use and create Thymis modules](./external-projects/thymis-modules.md), and [package software for deployment on devices](./external-projects/packaging-software.md).

If you want to make quick changes immediately, make sure to look at the [custom NixOS module](./external-projects/thymis-modules/nix-language-module.md) documentation, which allows you to write Nix code to configure your devices and software.

If you are setting up your project on new device types, you can refer to the [Adding a new Type of Device](./external-projects/add-new-device-type.md) guide for information on how to add support for new device types in Thymis.

## Examples of projects possible with Thymis

Thymis can be used to manage a wide range of projects. In this docs section, we will explore an example project that packages a QT6 application for deployment on Thymis-managed devices.

Other examples of projects that can be managed with Thymis include:
- **Web Applications**: Deploying web applications that can be accessed via a browser on the device or from other devices on the network.
- **IoT Applications**: Managing IoT devices and applications, allowing for remote data collection, device control, and monitoring.
- **Custom Software**: Packaging and deploying custom software solutions that require specific configurations or dependencies.
- **Kiosk Applications**: Setting up devices in kiosk mode to run specific applications, such as digital signage or interactive displays.
- **Containerized Applications**: Running applications in containers, allowing for easy deployment and management of software across different devices.

Further, when extending Thymis with custom Nix code or integrating new device types such as VM environments, other applications are possible, such as:
- **Virtual Machine Management**: Using Thymis to manage virtual machines, allowing for easy deployment and configuration of environments onto various target hosts.
- **Quick Prototyping**: Setting up virtual machines for rapid prototyping and testing of new software or configurations before deploying them to physical devices.
- **Development Machines**: Using Thymis to manage development environments, allowing developers to quickly spin up and configure VMs or Hardware devices for testing and development purposes.

## Rough draft of integration steps

Integration of your project into Thymis typically requires the following:

- You have a project or prototype that you want to deploy on Linux devices managed by Thymis.

Once you have your project ready, you can follow these steps to integrate it into Thymis:

- **Package your project**: Use Nix to package your project, ensuring it can be built and deployed on the target devices. This may involve creating a Nix expression that defines how to build and install your software. While this is described in detail in the [Packaging Software](./external-projects/packaging-software.md) section, you can test packages on your device without packaging your software by using a [Custom NixOS Module](./external-projects/thymis-modules/nix-language-module.md), or by using the built-in [Thymis Modules](./external-projects/thymis-modules.md).
- **Create a Thymis Module**: If your project requires specific configurations or dependencies, create a Thymis Module that defines how to deploy and manage your software on the devices. This module can include settings for the device, such as network configurations, software dependencies, and any other necessary parameters. See [Creating your first Thymis Module](./external-projects/thymis-modules/first-module.md) for a guide on how to create your first Thymis Module.
- **Add your project to Thymis**: Once your project is packaged and the Thymis Module is created, you can add your project to Thymis. This typically involves creating a specially prepared Git repository that contains your Nix expressions and Thymis Module. You can then configure Thymis to use this repository as an external project. Once set up, you can add modules from your project to Thymis device configurations or tags, allowing you to apply your project configurations to devices managed by Thymis.
  See the [Setting up external repositories](./external-projects/external-repositories.md) guide for more information on how to set up your project repository.
- **Deploy your project**: After adding your project to Thymis, you can deploy it to devices. This involves selecting the devices you want to target and applying the modules from your project to those devices. Thymis will handle the deployment process, ensuring that your software is installed and configured correctly on the target devices. See the [Deploy an Update](./device-lifecycle/update.md) guide for more information on how to deploy updates to devices.
- **Manage and update your project**: Once your project is deployed, you can manage it through Thymis. This includes updating the software, changing configurations, and monitoring the status of the devices. You can also use Thymis to roll back changes if necessary, ensuring that your devices remain stable and functional. See the [Troubleshooting](./device-lifecycle/troubleshooting.md) guide for more information on how to troubleshoot issues with your project and devices.
