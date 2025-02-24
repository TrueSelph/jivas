
# JIVAS

![GitHub release (latest by date)](https://img.shields.io/github/v/release/TrueSelph/jivas)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/TrueSelph/jivas/test-jivas.yaml)
![GitHub issues](https://img.shields.io/github/issues/TrueSelph/jivas)
![GitHub pull requests](https://img.shields.io/github/issues-pr/TrueSelph/jivas)
![GitHub](https://img.shields.io/github/license/TrueSelph/jivas)

`jivas` is an Agentic Framework for rapidly prototyping and deploying graph-based, AI solutions.

## Installation

To install `jivas`, use `pip`:

```sh
pip install jivas
```

## Usage

To use `jivas`, you can start the framework with the following command:

```sh
jac jvserve <path-to-your-jac-file>
```

For example:

```sh
jac jvserve main.jac
```

### Supported Arguments

- `--host`: The host to run the server on. Default is `
- `--port`: The port to run the server on. Default is `8000`.
- `--loglevel`: The logging level to use. Default is `INFO`.

Example with all arguments:

```sh
jac jvserve main.jac --host 0.0.0.0 --port 8000 --loglevel DEBUG
```

## API Endpoints

- **Interact with Agent**: `/interact` (POST)
- **Execute Webhook**: `/webhook/{key}` (GET, POST)
- **Execute Action Walker**: `/action/walker` (POST)

You can see all endpoints at the URL `/docs`.

## 🔰 Contributing

- **🐛 [Report Issues](https://github.com/TrueSelph/jivas/issues)**: Submit bugs found or log feature requests for the `jivas` project.
- **💡 [Submit Pull Requests](https://github.com/TrueSelph/jivas/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your GitHub account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/TrueSelph/jivas
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to GitHub**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details open>
<summary>Contributor Graph</summary>
<br>
<p align="left">
    <a href="https://github.com/TrueSelph/jivas/graphs/contributors">
        <img src="https://contrib.rocks/image?repo=TrueSelph/jivas" />
   </a>
</p>
</details>

## 🎗 License

This project is protected under the Apache License 2.0. See [LICENSE](./LICENSE) for more information.

## Additional Information

Since `jivas` is a framework for AI solutions, it supports various integrations and extensions. You can find more information about its capabilities and extensions in the official documentation.
