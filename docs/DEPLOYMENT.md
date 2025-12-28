# Documentation Deployment

This project uses GitHub Actions to automatically deploy MkDocs documentation to GitHub Pages.

## Automatic Deployment

Documentation is automatically deployed when:
- Changes are pushed to the `main` branch
- Files in `docs/`, `mkdocs.yml`, or `.github/workflows/docs.yml` are modified

## Manual Deployment

You can manually trigger deployment from the GitHub Actions tab:
1. Go to the "Actions" tab in your GitHub repository
2. Select "Deploy Documentation" workflow
3. Click "Run workflow"

## Initial Setup

To enable GitHub Pages for the first time:

1. Go to your repository settings
2. Navigate to "Pages" in the left sidebar
3. Under "Source", select "GitHub Actions"
4. Save the settings

The workflow will automatically deploy to `https://<username>.github.io/pytest_gxp`

## Local Testing

Before pushing, test the documentation locally:

```bash
just docs-serve
```

Visit `http://127.0.0.1:8000` to preview the documentation.

## Troubleshooting

If deployment fails:
1. Check the GitHub Actions logs for errors
2. Verify `mkdocs.yml` is valid: `mkdocs build`
3. Ensure all required dependencies are listed in the workflow file
4. Check that GitHub Pages is enabled in repository settings

