import asyncio

from heurist_python_sdk import Heurist
from utils import load_env


async def basic_image_generation(client):
    response = await client.images.generate(
        {
            "model": "FLUX.1-dev",
            "prompt": "A serene landscape with mountains and a lake",
        }
    )
    print(f"Basic image generated: {response['url']}")
    return response["url"]


async def advanced_image_generation(client):
    response = await client.images.generate(
        {
            "model": "FLUX.1-dev",
            "prompt": "A futuristic cityscape at night with flying cars",
            "neg_prompt": "blurry, low quality, distorted",
            "num_iterations": 30,
            "guidance_scale": 7.5,
            "width": 768,
            "height": 512,
            "seed": 12345,
            "job_id_prefix": "custom-job",
        }
    )
    print(f"Advanced image generated: {response['url']}")
    return response["url"]


async def batch_generation(client):
    prompts = [
        "A peaceful garden with blooming flowers",
        "A stormy ocean with lightning",
        "A cozy cabin in snowy woods",
    ]

    results = []
    for prompt in prompts:
        response = await client.images.generate(
            {"model": "FLUX.1-dev", "prompt": prompt, "width": 512, "height": 512}
        )
        results.append({"prompt": prompt, "url": response["url"]})
        print(f"Generated image for '{prompt}': {response['url']}")

    return results


async def zeek_model_generation(client):
    response = await client.images.generate(
        {
            "model": "Zeek",
            "prompt": "Zeek style illustration of a magical forest",
            "width": 512,
            "height": 512,
        }
    )
    print(f"Zeek model image generated: {response['url']}")
    return response["url"]


async def main():
    load_env()
    client = Heurist()

    try:
        print("1. Basic Image Generation")
        await basic_image_generation(client)

        print("\n2. Advanced Image Generation")
        await advanced_image_generation(client)

        print("\n3. Batch Generation")
        await batch_generation(client)

        print("\n4. Zeek Model Generation")
        await zeek_model_generation(client)

        # TODO: add philand model

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
