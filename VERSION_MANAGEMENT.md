# Version Management

This project follows modern Python packaging standards for version management.

## Single Source of Truth

The version is defined **only** in `pyproject.toml`:

```toml
[project]
name = "quantjourney-bidask"
version = "0.9.5"
```

## How Version is Accessed

The package imports version dynamically from package metadata:

```python
# In quantjourney_bidask/__init__.py
try:
    from importlib.metadata import version
    __version__ = version("quantjourney-bidask")
except ImportError:
    # Fallback for development mode
    __version__ = "0.9.5"
```

## Why This Approach?

### ✅ Advantages:
- **Single source of truth** - no version synchronization issues
- **Modern standard** - follows PEP 621 (pyproject.toml standard)
- **Automatic consistency** - pip/build tools read from same source
- **Less maintenance** - only update one file for releases

### ❌ Old approach problems:
- **Version drift** - `_version.py` and `pyproject.toml` can get out of sync
- **Extra maintenance** - need to update multiple files
- **Build inconsistency** - different tools might read different versions

## Version Update Process

1. **Update version in `pyproject.toml`**:
   ```toml
   version = "0.9.6"
   ```

2. **Reinstall in development mode**:
   ```bash
   pip install -e .
   ```

3. **Verify version**:
   ```python
   import quantjourney_bidask
   print(quantjourney_bidask.__version__)  # Should show new version
   ```

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md if exists
- [ ] Test package: `pip install -e .`
- [ ] Build: `python -m build`
- [ ] Upload to PyPI: `twine upload dist/*`

## Files Involved

- ✅ `pyproject.toml` - **Primary version source**
- ✅ `quantjourney_bidask/__init__.py` - **Dynamic import**
- ❌ `_version.py` - **Removed** (no longer needed)

This ensures version consistency and follows modern Python packaging best practices.