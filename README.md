# Heurist Python SDK

An unofficial Python SDK for the Heurist API, adapted fully from the official [typescript version](https://github.com/heurist-network/heurist-sdk/).

## Installation

```bash
git clone https://github.com/rexdotsh/heurist-python-sdk.git
cd heurist-python-sdk
pip install -e .
```

## Quick Start

```python
import asyncio
from heurist_python_sdk import ClientOptions, Heurist

async def main():
    # initialize client with api key
    client = Heurist(ClientOptions(apiKey="your-api-key-here"))

    # generate an image!
    response = await client.images.generate(
        {
            "model": "FLUX.1-dev",
            "prompt": "A serene landscape with mountains and a lake",
        }
    )
    print(f"Generated image URL: {response['url']}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Features

### Image Generation

Generate images using various models with customizable parameters:

```python
response = await client.smartgen.generate_image(
    {
        "description": "A magical forest at twilight",
        "stylization_level": 4,  # 1-5
        "detail_level": 5,  # 1-5
        "color_level": 4,  # 1-5
        "lighting_level": 3,  # 1-5
    }
)
```

### Smart Generation

Enhanced image generation with automatic prompt optimization:

```python
response = await client.smartgen.generate_image({
    'description': 'A magical forest at twilight',
    'stylization_level': 4,  # 1-5
    'detail_level': 5,       # 1-5
    'color_level': 4,        # 1-5
    'lighting_level': 3      # 1-5
})
```

## Configuration

### Environment Variables

The SDK supports these environment variables:

- `HEURIST_API_KEY`: Your Heurist API key (required)
- `HEURIST_BASE_URL`: Base URL for API (optional, defaults to `http://sequencer.heurist.xyz`)
- `HEURIST_WORKFLOW_URL`: Workflow service URL (optional)

### Smart Generation

```python
response = await client.smartgen.generate_image(
    {
        "description": "A cyberpunk city",
        "image_model": "FLUX.1-dev",
        "language_model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "is_sd": True,
        "must_include": "neon lights, rain",
        "examples": [
            "cyberpunk street, neon signs, rain-slicked streets",
            "futuristic urban landscape, holographic advertisements",
        ],
        "negative_prompt": "blurry, low quality",
        "quality": "high",  # or 'normal'
        "guidance_scale": 7.5,
        "param_only": False,  # Set to True to only get parameters without generating
    }
)
```

## Examples

Find more examples in the [`examples/`](examples/) directory:

- [Basic Image Generation](examples/image_generation.py)
- [Smart Image Generation](examples/smart_generation.py)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This SDK is distributed under the MIT license. See LICENSE file for details.
