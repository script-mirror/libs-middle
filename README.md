# Raizen Power Trading Libraries - Middle Layer

Middle layer utilities for Raizen Power Trading applications.

## Installation

You can install this library directly from GitHub using pip:

```bash
pip install git+https://github.com/your-username/raizen-power-trading-libs-middle.git
```

Or for a specific branch/tag:

```bash
pip install git+https://github.com/your-username/raizen-power-trading-libs-middle.git@main
```

## Usage

```python
from middle import sanitize_string

# Basic usage
text = "Héllo Wörld! @#$"
sanitized = sanitize_string(text)
print(sanitized)  # Output: "HELLO WORLD"

# With custom characters
text = "test-string_with-dashes"
sanitized = sanitize_string(text, custom_chars="-_")
print(sanitized)  # Output: "TEST-STRING_WITH-DASHES"
```

## Functions

### `sanitize_string(text, custom_chars="")`

Sanitizes a string by removing special characters and normalizing the text.

**Parameters:**
- `text` (str): Text to be sanitized
- `custom_chars` (str): Additional characters to allow in the output

**Returns:**
- `str`: Sanitized string in uppercase

## Development

To install in development mode:

```bash
git clone https://github.com/your-username/raizen-power-trading-libs-middle.git
cd raizen-power-trading-libs-middle
pip install -e .[dev]
```

## License

MIT License