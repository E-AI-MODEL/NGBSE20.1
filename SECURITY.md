# Security Policy

## Supported Versions

NGBSE follows semantic versioning and provides security updates for the following versions:

| Version | Supported          | End of Life |
| ------- | ------------------ | ----------- |
| 20.2.x  | :white_check_mark: | TBD         |
| 20.1.x  | :white_check_mark: | 2024-06-01  |
| 18.0.x  | :white_check_mark: | 2024-03-01  |
| < 18.0  | :x:                | 2023-12-01  |

## Security Features

### Supply Chain Security
- **SBOM Generation**: Automated Software Bill of Materials (SBOM) generation using CycloneDX and SPDX formats
- **Dependency Scanning**: Continuous vulnerability scanning with Safety and Bandit
- **Locked Dependencies**: Pinned dependency versions in `requirements.lock`
- **Docker Security**: Multi-stage builds with minimal attack surface

### Credential Management
- **Environment Variables**: All API credentials stored in environment variables
- **No Hardcoded Secrets**: Zero hardcoded credentials in source code
- **Credential Validation**: Automatic validation before collector activation
- **Secret Rotation**: Support for credential rotation without code changes

### Input Validation
- **Seed Sanitization**: All input seeds validated and sanitized
- **Rule Validation**: Rule conditions validated before execution
- **STIX Sanitization**: Output sanitization for STIX bundles
- **Type Checking**: Comprehensive type checking with MyPy

### Runtime Security
- **Error Handling**: Graceful error handling prevents information disclosure
- **Logging Security**: Sensitive data excluded from logs
- **Resource Limits**: Configurable resource limits prevent DoS
- **Sandboxing**: Docker-based execution environment

## Reporting a Vulnerability

### How to Report
We take security vulnerabilities seriously. If you discover a security vulnerability in NGBSE, please report it responsibly:

1. **Email**: Send details to security@ngbse.org
2. **Encryption**: Use our PGP key for sensitive reports (key ID: `0x1234567890ABCDEF`)
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested remediation (if any)

### Response Timeline
- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Resolution**: Within 30 days (or coordinated disclosure timeline)
- **Public Disclosure**: After fix is available and tested

### Vulnerability Disclosure Policy
We follow responsible disclosure practices:

1. **Private Disclosure**: Vulnerabilities are kept private until a fix is available
2. **Coordinated Disclosure**: We work with reporters on disclosure timing
3. **Credit**: Security researchers are credited (unless they prefer anonymity)
4. **No Legal Action**: Good faith security research will not result in legal action

### Security Advisories
Security advisories are published in:
- GitHub Security Advisories
- Project documentation
- Release notes
- Security mailing list

## Security Best Practices

### For Users
- **Keep Updated**: Always use the latest version
- **Credential Security**: Use strong, unique API keys
- **Environment Isolation**: Run in isolated environments
- **Monitor Logs**: Regularly review logs for suspicious activity
- **Access Control**: Limit access to configuration and output files

### For Developers
- **Code Review**: All code changes require security review
- **Dependency Updates**: Regular dependency updates and vulnerability scanning
- **Testing**: Comprehensive security testing in CI/CD pipeline
- **Documentation**: Security considerations documented in code

### For Integrators
- **API Security**: Use HTTPS for all API communications
- **Authentication**: Implement proper authentication for API access
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Monitoring**: Monitor for unusual patterns or errors

## Security Tools and Scanning

### Automated Scanning
- **Bandit**: Python security linting
- **Safety**: Dependency vulnerability scanning
- **Trivy**: Container vulnerability scanning
- **CodeQL**: GitHub's semantic code analysis

### Manual Security Review
- **Code Review**: All changes reviewed for security implications
- **Penetration Testing**: Regular penetration testing of releases
- **Threat Modeling**: Threat modeling for new features
- **Security Architecture Review**: Regular architecture security reviews

## Compliance and Standards

### Standards Compliance
- **STIX 2.1**: Full compliance with STIX 2.1 specification
- **CycloneDX**: SBOM generation following CycloneDX standard
- **SPDX**: Alternative SBOM format support
- **OWASP**: Following OWASP security guidelines

### Regulatory Considerations
- **GDPR**: Privacy considerations for data processing
- **SOC 2**: Security controls alignment
- **ISO 27001**: Information security management alignment
- **NIST**: Cybersecurity framework alignment

## Security Contacts

- **Security Team**: security@ngbse.org
- **PGP Key**: Available at https://ngbse.org/security/pgp-key.asc
- **Security Mailing List**: security-announce@ngbse.org
- **Bug Bounty**: Currently not running a formal program

## Security Changelog

### 20.2.0-GA
- Added comprehensive security scanning in CI/CD
- Implemented SBOM generation
- Enhanced credential management
- Added security-focused documentation

### 20.1.0
- Initial security policy implementation
- Basic vulnerability scanning
- Credential environment variable support

### 18.0.0-GA
- Initial security considerations
- Basic input validation
- STIX output sanitization
