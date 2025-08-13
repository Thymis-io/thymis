# Secrets

In Thymis, a **Secret** is a secure way to manage sensitive information such as passwords, API keys, certificates, and other confidential data that needs to be deployed to devices. Secrets are stored in the database encrypted at rest, ensuring that sensitive information remains protected even if the database is compromised.

## Secret Storage and Security

Thymis uses `(r)age` for encryption, providing strong security guarantees. Secrets are encrypted in the database and only decrypted when needed during deployment to devices. For optimal security, secrets are decrypted to `/run/` directories, which are typically located in RAM and not written to persistent storage.

## Secret Types

Thymis supports several types of secrets to accommodate different use cases:

- **Single-line**: Simple text secrets
- **Multi-line**: Secrets that span multiple lines, such as private keys or certificates
- **Environment variables**: Secrets formatted as environment variables
- **Files**: Secrets stored as files on the target device

## Secret Processing

Thymis provides post-processing capabilities for secrets:

- **None**: No post-processing applied
- **mkpasswd-yescrypt**: Processes secrets into password hashes using yescrypt

This allows secrets to be automatically transformed into the format needed by applications while keeping the original secret secure.

## Secret References

When integrating with an application, you reference a secret by specifying the path where it should be decrypted on the device (e.g., `/run/my-secret`). We recommend decrypting secrets to `/run/` directories to ensure they reside in RAM and not on persistent storage.

## Device Images

Secrets can be included in device images during the initial deployment. When a secret is included in a device image:
- It's encrypted with a symmetric key during the image creation
- After deployment to a device, the secret is re-encrypted with the device's public key
- This ensures that secrets remain secure even in static device images

## Secret Management

Secrets can be managed through the Secrets page in the Thymis UI or created directly in configuration forms when needed. Secrets can also be shared across devices using Tags, allowing you to apply the same secret to multiple device configurations.

## Security Best Practices

- Use appropriate post-processing for passwords
- Limit the number of devices that have access to a secret
- Rotate secrets regularly
- Monitor secret usage for any anomalies
- Consider the security implications when including secrets in device images

## Troubleshooting

For advanced troubleshooting, you can use the terminal to verify secret deployment:
- Check if secrets are properly decrypted at their specified paths using `cat /run/your-secret-path`
- Verify permissions and ownership of secret files
- Monitor system logs for any secret-related errors

## See also
- [Deploying Secrets to devices](../../device-lifecycle/secrets.md)
- [Creating Your First Thymis Module](../../external-projects/thymis-modules/first-module.md)
- [Accessing the Terminal](../../device-lifecycle/ssh-terminal.md)
