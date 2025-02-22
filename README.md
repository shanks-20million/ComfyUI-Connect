# ⚡ ComfyUI Fast API

Transform your ComfyUI to a powerful API, serving all your saved workflows into ready to use HTTP endpoints.

> **WIP Warning** heavy development and not fully battle-tested, this package may contain bugs, please do not use in production for now.

**Key features :**

- **✨ Plug and play** - Automatically serve your ComfyUI workflows into `/api/workflows/*`
- **🏷️ Annotations** - Expose your inputs and outputs by `[tagging]` your node names.
- **⚡ Fast** - No added overload, powerful node caching.

**Planned :**

- **📖 OpenAPI Documentation** - Automated OpenAPI documentation of all available workflows.
- **🔀 Load Balancer** - Connect each ComfyUI instance to a Load Balancer, features :
  - Workflow syncing between all instances.
  - Heartbeat and speed priority check for best request routing
  - Maybe a small UI for statistics about instances, runs ?
  - I am working on this on a separate project, stay tuned

## Installation

Install by cloning this project into your `custom_nodes` folder.

```
cd custom_nodes
git clone https://github.com/IfnotFR/ComfyUI-Fast-API.git
```

## Quick Start

1. Annotate editable inputs, for example rename the `KSampler` by `KSampler [my sampler]`

2. Annotate your output, for example `Preview Image` into `Preview Image [my awesome image]`.

3. Click on `Workflow > Save API Endpoint`, write your endpoint name, you can now run it by doing a `POST /api/workflows/ENDPOINT_NAME`.

**Example Request :**

`POST /api/workflows/ENDPOINT_NAME`

```
{
  "my sampler": {
    seed: 1234
  }
}
```

**Example Response (base64) :**

```
{
  "my awesome image": [
    "V2VsY29tZSB0byA8Yj5iYXNlNjQuZ3VydTwvYj4h..."
  ]
}
```

## Annotations

### Free Annotations

- `[my-node]`: Annotate editable nodes or output nodes.
- `[my-sampler:seed,steps,cfg]`: Limit exposed inputs of annoted nodes.

### Internal Annotations

- `[!bypass]`: Bypass this node when running from API (but keep it in ComfyUI).
  - Usefull if you want to lighten your workflow from your debug nodes when running from API.
- `[!cache]`: Globally register this node to be included on each API call.
  - It allows you to keep the node in memory, denying ComfyUI to unload it. See How to cache models.

## Uploading images

**From URL :**

`POST /api/workflows/ENDPOINT_NAME`

```
{
  "input": {
    "image": {
      "type": "file",
			"url": "V2VsY29tZSB0byA8Yj5iYXNlNjQuZ3VydTwvYj4h ..."
    }
  }
}
```

**From Base64 :**

`POST /api/workflows/ENDPOINT_NAME`

```
{
  "input": {
    "image": {
      "type": "file",
      "name": "my-file.png"
			"content": "https://foo.bar/image.png"
    }
  }
}
```

## How to cache models

Imagine you have two workflows `a.json` and `b.json`, each loading a different model (two different `Load Checkpoint` nodes loading `dreamshaper.safetensors` and `juggernaut.safetensors`).

Running `a.json` will :

- Load `dreamshaper.safetensors` into VRAM
- Execute the rest ...

Then, running `b.json` will :

- Unload `dreamshaper.safetensors` from VRAM
- Load `juggernaut.safetensors` into VRAM
- Execute the rest ...

Finally, running `a.json` again will :

- Unload `juggernaut.safetensors` from VRAM
- Load `dreamshaper.safetensors` into VRAM
- Execute the rest ...

By putting `[!cache]` annotation on both `Load Checkpoint` workflows you will instruct ComfyUI to **force them to stay in memory** reducing loading times (but increasing VRAM usage).

Now, running `a.json` will :

- Load `dreamshaper.safetensors` into VRAM
- Load `juggernaut.safetensors` into VRAM
- Execute the rest ...

Then, running `b.json` will :

- Execute the rest ...

Then, running `a.json` will :

- Execute the rest ...

> **Note :** Caching is not limited to `Load Checkpoint`. Each node keeping stuff in memory like models will benefit from caching. For example : `Load ControlNet Model`, `SAM2ModelLoader`, `Load Upscale Model`, etc ...

## TODO

- [] Find a way to hook the save event, for replacing the "Save API Endpoint" step for updating workflows
- [] Default configuration should be loaded from environment (paths, endpoint ...)
- [] Editable configuration (from the ComfyUI config interface ?)
- [] Test edge cases like image batches, complex workflows ...
- [] Output as download url instead of base64 option, for bigger files

## Why This ?

ComfyUI ecosystem is actually working to solve the deployment and scalability approach when it comes to run ComfyUI Workflows, but ...

**Working with JSON workflows has limitations**

- Complicated json file versionning, and it is a pain to export each time you do a modification.
- I can be a challenge to edit workflows on the fly by your app (specially for bypassing nodes etc ...)

**Pusing workflows into clouds** ([ComfyDeploy](https://comfydeploy.com/), [RunComfy](https://www.runcomfy.com/), [Replicate](https://replicate.com/), [RunPod](https://www.runpod.io/) etc ...) **can have insane speed issues, hard pricing, and features limitations**

- Simple workflows of 5s can take 15s, 30s and up to minutes due to cold start and the provider queue system overload.
- In managed cloud it can be faster without cold start, but you are limited to available models, custom nodes, etc ...

---

Made with ❤️ by Ifnot.
