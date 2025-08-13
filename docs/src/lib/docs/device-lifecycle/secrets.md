# Deploying Secrets to devices

This guide explains how to create, manage, and deploy secrets to your devices using Thymis.

## Creating Secrets

You can create secrets in two ways:
1. Through the dedicated Secrets page
2. Directly in configuration forms when needed

To create a secret through the Secrets page:

1. Navigate to the **Secrets** page in the sidebar
2. Click the **Create Secret** button
3. Fill in the secret details:
   - **Name**: A descriptive name for the secret
   - **Type**: Choose from single-line, multi-line, environment variables, or files
   - **Post-processing**: Select appropriate processing (None or mkpasswd-yescrypt for passwords)
   - **Content**: Enter the secret value
4. Click **Create**

![Creating a Secret](./secret-creation-form.png)
## Using Secrets in Configurations

To use secrets in your device configurations:

1. Navigate to the **Configs** page
2. Select a device configuration or create a new one
3. Add the **Core Device Configuration** module to your configuration
4. In the module's settings, find the **Secrets** section
5. Click **Add Secret**
6. Select the secret you want to use and specify where it should be deployed on the device
7. Click **Apply**

## Using Secrets with Tags

To share secrets across multiple devices:

1. Navigate to the **Config-Tags** page
2. Click **Create Tag**
3. Add the **Core Device Configuration** module to the tag
4. In the module's settings, add secrets as described above
5. Apply the tag to device configurations that need these secrets

## Secret Types and Use Cases

### Single-line Secrets
- **Use case**: API keys, simple passwords, tokens
- **Example**: `api-key = "abcd1234"`

### Multi-line Secrets
- **Use case**: Private keys, certificates, configuration files
- **Example**:
  ```
  -----BEGIN PRIVATE KEY-----
  MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgw...
  -----END PRIVATE KEY-----
  ```

### Environment Variables
- **Use case**: Application configuration with environment variables
- **Example**:
  ```
  DB_PASSWORD=mysecretpassword
  API_TOKEN=abcd1234
  ```

### Files
- **Use case**: Storing certificates, custom configuration files
- **Example**: Deploying a certificate file at `/run/secrets/cert.pem`

## Post-processing Options

### None
Use this for secrets that don't need additional processing, such as API keys or tokens.

### mkpasswd-yescrypt
Use this for passwords to transform them into secure hashes. This is especially useful when you need to set user passwords.

## Deploying Secrets to Devices

Once you've configured secrets for your devices:

1. Click **Commit** in the toolbar to save your changes
2. Click **Build** to verify the configuration builds successfully
3. Click **Deploy** and select the devices or tags you want to deploy to
4. Thymis will securely deploy the secrets to the specified locations on your devices

## Security Considerations

- Secrets are decrypted to `/run/` directories by default, which are in RAM and not persisted
- When including secrets in device images, they're encrypted with a symmetric key during image creation and then re-encrypted per device
- Regularly review which devices have access to which secrets
- Consider using different secrets for different environments or device types

## Troubleshooting

If secrets aren't deployed correctly:
1. Check that the secret exists and is correctly configured
2. Verify the deployment path exists and has appropriate permissions
3. Check the logs in the Tasks view for error messages
4. Use the terminal to verify secret deployment:
   - Check if secrets are properly decrypted at their specified paths using `cat /run/your-secret-path`
   - Verify permissions and ownership of secret files
   - Monitor system logs for any secret-related errors

## See also
- [Secrets concept](../../reference/concepts/secret.md)
- [Device Configuration](../../external-projects/thymis-modules/first-module.md)
- [Deploying Files using Artifacts](./artifacts.md)
- [Deploy an Update](./update.md)
