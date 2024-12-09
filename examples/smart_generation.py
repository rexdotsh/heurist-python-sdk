import asyncio

from heurist_python_sdk import Heurist
from utils import load_env


async def basic_smart_generation(client):
    response = await client.smartgen.generate_image(
        {"description": "A magical forest at twilight"}
    )
    print(f"Basic smart generation result: {response['url']}")
    print(f"Generated parameters: {response['parameters']}")
    return response


async def advanced_smart_generation(client):
    response = await client.smartgen.generate_image(
        {
            "description": "A cyberpunk city street at night",
            "width": 768,
            "height": 512,
            "image_model": "FLUX.1-dev",
            "language_model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "is_sd": True,
            "must_include": "neon lights, rain",
            "examples": [
                "cyberpunk street, neon signs, rain-slicked streets, towering skyscrapers",
                "futuristic urban landscape, holographic advertisements, steam rising",
            ],
            "negative_prompt": "blurry, low quality, distorted",
            "quality": "high",
            "guidance_scale": 7.5,
            "stylization_level": 4,
            "detail_level": 5,
            "color_level": 5,
            "lighting_level": 4,
        }
    )
    print(f"Advanced smart generation result: {response['url']}")
    print(f"Generated parameters: {response['parameters']}")
    return response


async def style_variations(client):
    styles = [
        {
            "description": "A peaceful mountain landscape",
            "stylization_level": 1,  # Photorealistic
            "detail_level": 4,  # Rich in details
            "color_level": 3,  # Natural colors
            "lighting_level": 2,  # Soft lighting
        },
        {
            "description": "A peaceful mountain landscape",
            "stylization_level": 4,  # Clearly stylized
            "detail_level": 2,  # Clean and simple
            "color_level": 5,  # Hyper-saturated
            "lighting_level": 4,  # Dramatic lighting
        },
        {
            "description": "A peaceful mountain landscape",
            "stylization_level": 5,  # Highly abstract
            "detail_level": 1,  # Minimalist
            "color_level": 1,  # Monochromatic
            "lighting_level": 5,  # Extreme dramatic
        },
    ]

    results = []
    for style in styles:
        response = await client.smartgen.generate_image(style)
        results.append(
            {
                "style": style,
                "url": response["url"],
                "parameters": response["parameters"],
            }
        )
        print(f"\nGenerated image with style variation:")
        print(f"Style settings: {style}")
        print(f"Result URL: {response['url']}")

    return results


async def prompt_only_example(client):
    response = await client.smartgen.generate_image(
        {
            "description": "A serene Japanese garden in autumn",
            "stylization_level": 3,
            "detail_level": 4,
            "color_level": 4,
            "lighting_level": 3,
            "param_only": True,  # Only return the parameters without generating
        }
    )
    print("\nGenerated parameters without image:")
    print(f"Enhanced prompt: {response['parameters']['prompt']}")
    return response["parameters"]


async def stable_diffusion_example(client):
    response = await client.smartgen.generate_image(
        {
            "description": "A majestic dragon soaring through storm clouds",
            "is_sd": True,
            "must_include": "dragon, storm",
            "negative_prompt": "(worst quality:1.4), bad quality, nsfw",
            "quality": "high",
            "stylization_level": 4,
            "detail_level": 5,
            "color_level": 4,
            "lighting_level": 5,
        }
    )
    print(f"\nStable Diffusion format result: {response['url']}")
    print(f"Generated parameters: {response['parameters']}")
    return response


async def main():
    load_env()

    client = Heurist()

    try:
        print("1. Basic Smart Generation")
        await basic_smart_generation(client)

        print("\n2. Advanced Smart Generation")
        await advanced_smart_generation(client)

        print("\n3. Style Variations")
        await style_variations(client)

        print("\n4. Prompt-Only Generation")
        await prompt_only_example(client)

        print("\n5. Stable Diffusion Format")
        await stable_diffusion_example(client)

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
