# Changelog

All notable changes to NGBSE will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [20.2.1] - 2024-01-XX

### Added
- **Scoring v18.1**: New source trust and keyword pattern scoring
  - Source trust scoring based on domain trustworthiness
  - Keyword pattern scoring with configurable rules
  - Shadow mode for safe rollout and comparison
  - Enhanced observability with detailed metrics
  - Gradual rollout configuration stages
- **Configuration Schema**: New `sources.json` schema for domain trust levels
- **Enhanced CI/CD**: Added config validation and golden tests
- **Comprehensive Documentation**: Scoring v18.1 guide and migration docs

### Changed
- **Scoring Configuration**: Added v18.1 flags (backward compatible)
- **Score Output**: Enhanced breakdown format with new fields
- **Configuration Validation**: Stricter schema validation for config files

## [20.2.0-GA] - 2024-01-XX

### Added
- **Modular Architecture**: Complete refactoring of the orchestrator into separate, testable components
- **ConfigLoader**: Centralized configuration management with credential handling
- **CollectorManager**: Unified collector lifecycle management with credential validation
- **PipelineStages**: Modular pipeline stages for better testability and maintainability
- **BALLM Integration**: Meta-layer generation with epistemic humility scoring
- **Comprehensive Testing**: Unit tests, integration tests, and test fixtures
- **CI/CD Pipeline**: GitHub Actions workflow with linting, testing, security scanning, and SBOM generation
- **Documentation**: Complete architecture documentation and migration guide
- **Security Enhancements**: Dependency vulnerability scanning and SBOM generation
- **Docker Support**: Pre-built Docker images with multi-stage builds

### Changed
- **Repository Structure**: Cleaned up root directory, moved demos to examples/, centralized config
- **Orchestrator API**: New class-based API with backward compatibility function
- **Configuration**: Centralized configuration in `config/` directory
- **Error Handling**: Improved error handling and graceful degradation
- **Logging**: Enhanced structured logging with trace IDs

### Fixed
- **Memory Leaks**: Fixed potential memory leaks in collector implementations
- **Credential Handling**: Improved credential validation and error messages
- **STIX Export**: Enhanced STIX bundle generation with proper provenance
- **Test Coverage**: Added comprehensive test coverage for all major components

### Security
- **Dependency Scanning**: Automated vulnerability scanning with Safety
- **Code Security**: Bandit security linting integration
- **SBOM Generation**: CycloneDX and SPDX SBOM generation for supply chain security
- **Credential Security**: Environment variable-based credential management

### Removed
- **Legacy Code**: Removed deprecated collector implementations
- **Build Artifacts**: Cleaned up `.egg-info` and `__pycache__` directories
- **Duplicate Configs**: Consolidated duplicate configuration files

## [20.1.0] - 2023-12-XX

### Added
- Initial BALLM integration
- Multi-collector architecture
- STIX 2.1 export support
- Basic scoring engine

### Changed
- Migrated from monolithic to modular architecture
- Updated scoring algorithms

## [18.0.0-GA] - 2023-06-XX

### Added
- Initial release of NGBSE
- Basic collector framework
- Simple scoring system
- STIX export functionality

---

## Migration Guide

### From 18.0.0-GA to 20.2.0-GA

#### Configuration Changes
- **Old**: Configuration files scattered in root and `data/` directories
- **New**: All configuration centralized in `config/` directory
  - `config/ngbse.config.yml` - Main configuration
  - `config/rules.json` - Rules configuration
  - `config/seeds.jsonl` - Seeds configuration

#### API Changes
- **Old**: Direct function calls to `run_pipeline()`
- **New**: Class-based API with `PipelineOrchestrator`
  ```python
  # Old way (still supported)
  result = run_pipeline(seeds, rules, metrics, config)
  
  # New way (recommended)
  orchestrator = PipelineOrchestrator("config")
  result = orchestrator.run_pipeline()
  ```

#### Environment Variables
- All API credentials now managed through environment variables
- No credentials in configuration files
- See `config/loader.py` for supported credential variables

#### Docker Usage
- **Old**: Manual Docker setup
- **New**: Pre-built images available
  ```bash
  docker run ngbse20:latest
  ```

### Breaking Changes
- Configuration file locations have changed
- Some internal APIs have been refactored
- Collector instantiation is now handled by CollectorManager

### Deprecations
- Direct collector instantiation (use CollectorManager)
- Inline configuration in function calls (use ConfigLoader)
- Manual credential management (use environment variables)