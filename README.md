# DeviantArt Sta.sh Uploader

A Python script to batch upload and publish images to DeviantArt Sta.sh with a real-time progress bar and automatic tag generation.

## Features

- **OAuth2 Authentication**: Securely obtain and store an access token.
- **Batch Upload**: Automatically find and upload all supported image files in the script directory.
- **Real-Time Progress**: Visualize upload progress for each file using `tqdm` and `requests-toolbelt`.
- **Auto-Generated Tags**: Parse each filename to extract a clean title and split into individual tags (no spaces). Include custom tags.
- **Automatic Publish**: Publish uploaded items to your DeviantArt gallery folder.
- **Error Handling**: Gracefully handle upload or publish failures with clear console output and manual fallback instructions.

## Requirements

- Python 3.7 or higher
- `requests`
- `tqdm`
- `requests-toolbelt`

Install dependencies via pip:

```bash
pip install requests tqdm requests-toolbelt
```

## Configuration

Edit the top of `upload.py` to set your credentials and preferences:

| Variable              | Description                                         
|-----------------------|-----------------------------------------------------
| `CLIENT_ID`           | Your DeviantArt OAuth2 Client ID                   
| `CLIENT_SECRET`       | Your DeviantArt OAuth2 Client Secret               
| `REDIRECT_URI`        | OAuth2 redirect URI (whitelisted in your app)      | `http://localhost:3000/callback`
| `FOLDER_ID`           | Gallery folder ID for publishing (or `None`)       
| `TAGS`                | List of base tags to include for each upload       
| `ACCESS_TOKEN_FILE`   | Path to store the OAuth access token               | `access_token.txt` |
| `IMAGE_EXTENSIONS`    | Tuple of supported image file extensions           | `(.jpg,.jpeg,.png,.gif)` |

## Usage

1. **Authorize**: On first run, the script will open your default browser. Grant the requested scopes (`stash`, `browse`, `publish`).
2. **Upload & Publish**: The script locates all images in its directory, uploads each with a progress bar, then publishes to your DeviantArt gallery.
3. **Manual Fallback**: If publishing fails (e.g., missing permission), a Sta.sh URL is printed for manual submission.

Run the script:

```bash
python upload.py
```

## Filename Parsing

Filenames should follow the pattern:

- `<name>`: Dash-separated segments.
- `<count>`: Number of images used in the mosaic.

The script will:

1. Clean and capitalize the `<name>`.
2. Split into individual tags (no spaces).
3. Use `<count>` in the description.

## Contributing

1. Fork this repository.
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -m "Add new feature"
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a Pull Request.

## License

MIT License. See [LICENSE](LICENSE) for details.

