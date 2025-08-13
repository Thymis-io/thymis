# Sharing settings via a tag

To avoid copying the same settings to multiple [configurations](../reference/concepts/configuration.md), you can use tags.

## Creating and Assigning a Tag

Navigate to the **Config-Tags** and click the **Create Tag** button.
Enter a name and press apply.

![Create a tag](./create-tag.png)

Next go to the **Configs** page and assign the tag to one or more devices.

![Assign tag](./assign-tag.png)

Your configurations should now look like this:

![Configs with tags](./configs-with-tags.png)

Any settings defined in the tag will be applied to all configurations that share this tag.

## Adding Settings to a Tag

Click on the tag to edit the settings.
We can add any module to the tag, here we add the **Core Device Configuration**.

![Add module to tag](./add-module-to-tag.png)
![Add Core Device Configuration](./add-core-device-configuration-module.png)

For example, we can set the WiFi SSID and password to be applied to all devices.
When adding a new device you only need a assign the tag and are done.
It makes sense to split up logical components in different tags like networking, specific applications, etc to reuse them when needed.

## Setting Priority

When the same module is used on both a tag and a config, the settings are merged or overridden depending on the context.
- Generally device settings take precedence
- Single values (e.g. WiFi SSID) are overwritten
- Lists (e.g. Authorized Keys) are merged

When moving a setting from a device configuration to a tag, remove any existing device-level value to ensure the tag's value is applied.
An empty value is still treated as a set value.
Click the x button on the right to clear the field:

![Overwritten setting](./overwritten-setting.png)
