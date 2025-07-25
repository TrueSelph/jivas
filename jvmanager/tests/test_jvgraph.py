"""Tests for the jvgraph launch command."""

from bson import ObjectId
from click.testing import CliRunner
from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from jvgraph.commands.launch import EndpointFactory, launch


class TestGraphLaunch:
    """Test cases for the launch command."""

    # Launch studio successfully on default port 8989
    def test_launch_jvgraph_default_port(self, mocker: MockerFixture) -> None:
        """Test launching launch with default port."""
        # Mock FastAPI and its dependencies
        mock_fastapi = mocker.patch("jvgraph.commands.launch.FastAPI")
        mock_app = mocker.MagicMock()
        mock_fastapi.return_value = mock_app

        # Mock uvicorn run
        mock_run = mocker.patch("jvgraph.commands.launch.run")

        # Mock Path operations
        mock_path = mocker.patch("pathlib.Path")
        mock_path_instance = mocker.MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.resolve.return_value.parent.parent.joinpath.return_value = (
            "mock/jvgraph/path"
        )

        # Mock click.echo
        mock_echo = mocker.patch("click.echo")

        # Create CLI runner
        runner = CliRunner()

        # Run the command
        result = runner.invoke(launch)

        # Verify the command executed successfully
        assert result.exit_code == 0

        # Verify proper port was used
        mock_run.assert_called_once_with(mock_app, host="0.0.0.0", port=8989)

        # Verify studio launch message was displayed
        mock_echo.assert_called_once_with("Launching Jivas Graph on port 8989...")

    def test_get_graph_endpoint(self, mocker: MockerFixture) -> None:
        """Test the /graph endpoint."""

        # Mock database collections
        mock_get_collection = mocker.patch(
            "jvgraph.commands.launch.NodeAnchor.Collection.get_collection"
        )
        mock_node_collection = mocker.MagicMock()
        mock_edge_collection = mocker.MagicMock()
        mock_get_collection.side_effect = lambda name: (
            mock_node_collection if name == "node" else mock_edge_collection
        )

        # Mock database responses
        mock_node_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ea"),
                "root": ObjectId("507f191e810c19729de860eb"),
                "architype": "TestNode",
                "name": "Node1",
            }
        ]
        mock_edge_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ec"),
                "root": ObjectId("507f191e810c19729de860eb"),
                "name": "Edge1",
                "source": "Node1",
                "target": "Node2",
                "architype": "TestEdge",
            }
        ]

        get_graph, _, __ = EndpointFactory.create_endpoints(False, None)

        # Create FastAPI app and test client
        app = FastAPI()
        app.add_api_route("/graph", endpoint=get_graph, methods=["GET"])
        client = TestClient(app)

        # Send GET request
        response = client.get("/graph", params={"root": "507f191e810c19729de860eb"})

        # Verify response
        assert response.status_code == 200
        expected_response = {
            "nodes": [
                {
                    "id": "507f191e810c19729de860ea",  # pragma: allowlist secret
                    "data": "TestNode",
                    "name": "Node1",
                }
            ],
            "edges": [
                {
                    "id": "507f191e810c19729de860ec",  # pragma: allowlist secret
                    "name": "Edge1",
                    "source": "Node1",
                    "target": "Node2",
                    "data": "TestEdge",
                }
            ],
        }
        assert response.json() == expected_response

    def test_get_users_endpoint(self, mocker: MockerFixture) -> None:
        """Test the /users endpoint."""

        # Mock database collections
        mock_get_collection = mocker.patch(
            "jvgraph.commands.launch.NodeAnchor.Collection.get_collection"
        )
        mock_user_collection = mocker.MagicMock()
        mock_get_collection.side_effect = lambda name: (
            mock_user_collection if name == "user" else None
        )

        # Mock database response
        mock_user_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ed"),
                "root_id": "507f191e810c19729de860eb",
                "email": "user@example.com",
            }
        ]

        _, get_users, __ = EndpointFactory.create_endpoints(False, None)

        # Create FastAPI app and test client
        app = FastAPI()
        app.add_api_route("/users", endpoint=get_users, methods=["GET"])
        client = TestClient(app)

        # Send GET request
        response = client.get("/users")

        # Verify response
        assert response.status_code == 200
        expected_response = [
            {
                "id": "507f191e810c19729de860ed",  # pragma: allowlist secret
                "root_id": "507f191e810c19729de860eb",
                "email": "user@example.com",
            }
        ]
        assert response.json() == expected_response

    def test_get_node_endpoint(self, mocker: MockerFixture) -> None:
        """Test the /graph/node endpoint."""

        # Mock database collections
        mock_get_collection = mocker.patch(
            "jvgraph.commands.launch.NodeAnchor.Collection.get_collection"
        )
        mock_node_collection = mocker.MagicMock()
        mock_edge_collection = mocker.MagicMock()
        mock_get_collection.side_effect = lambda name: (
            mock_node_collection if name == "node" else mock_edge_collection
        )

        # Mock database responses for connected nodes
        mock_edge_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ec"),
                "source": "507f191e810c19729de860ea",  # pragma: allowlist secret
                "target": "507f191e810c19729de860ed",  # pragma: allowlist secret
                "name": "Edge1",
                "architype": "TestEdge",
            }
        ]

        mock_node_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ed"),
                "name": "Node2",
                "architype": "TestNode",
            }
        ]

        _, __, get_node = EndpointFactory.create_endpoints(False, None)

        # Create FastAPI app and test client
        app = FastAPI()
        app.add_api_route("/graph/node", endpoint=get_node, methods=["GET"])
        client = TestClient(app)

        # Send GET request
        response = client.get(
            "/graph/node",
            params={"node_id": "507f191e810c19729de860ea", "depth": 1},
        )

        # Verify response
        assert response.status_code == 200
        expected_response = {
            "nodes": [
                {
                    "id": "507f191e810c19729de860ed",  # pragma: allowlist secret
                    "name": "Node2",
                    "data": "TestNode",
                }
            ],
            "edges": [
                {
                    "id": "507f191e810c19729de860ec",  # pragma: allowlist secret
                    "name": "Edge1",
                    "source": "507f191e810c19729de860ea",  # pragma: allowlist secret
                    "target": "507f191e810c19729de860ed",  # pragma: allowlist secret
                    "data": "TestEdge",
                }
            ],
        }
        assert response.json() == expected_response

    def test_auth_endpoints(self, mocker: MockerFixture) -> None:
        """Test that authentication works correctly."""
        # Mock HTTPBearer security
        security = HTTPBearer()

        # Mock NodeAnchor collection
        mock_get_collection = mocker.patch(
            "jvgraph.commands.launch.NodeAnchor.Collection.get_collection"
        )
        mock_user_collection = mocker.MagicMock()
        mock_get_collection.return_value = mock_user_collection

        # Mock decrypt function
        mock_decrypt = mocker.patch("jvgraph.commands.launch.decrypt")
        mock_decrypt.side_effect = [
            True,
            False,
        ]  # First call returns True, second False

        # Get endpoints with auth required
        get_graph, _, __ = EndpointFactory.create_endpoints(True, security)

        # Create FastAPI app and test client
        app = FastAPI()
        app.add_api_route("/graph", endpoint=get_graph, methods=["GET"])
        client = TestClient(app)

        # Test valid token
        response = client.get(
            "/graph",
            params={"root": "507f191e810c19729de860eb"},  # pragma: allowlist secret
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 200

        # Test invalid token
        response = client.get(
            "/graph",
            params={"root": "507f191e810c19729de860eb"},  # pragma: allowlist secret
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid token"}

    def test_get_graph_endpoint_auth(self, mocker: MockerFixture) -> None:
        """Test the /graph endpoint with authentication."""
        security = HTTPBearer()

        # Mock database collections
        mock_get_collection = mocker.patch(
            "jvgraph.commands.launch.NodeAnchor.Collection.get_collection"
        )
        mock_node_collection = mocker.MagicMock()
        mock_edge_collection = mocker.MagicMock()
        mock_get_collection.side_effect = lambda name: (
            mock_node_collection if name == "node" else mock_edge_collection
        )

        # Mock decrypt function
        mock_decrypt = mocker.patch("jvgraph.commands.launch.decrypt")
        mock_decrypt.side_effect = [
            True,
        ]

        # Mock database responses
        mock_node_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ea"),
                "root": ObjectId("507f191e810c19729de860eb"),
                "architype": "TestNode",
                "name": "Node1",
            }
        ]
        mock_edge_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ec"),
                "root": ObjectId("507f191e810c19729de860eb"),
                "name": "Edge1",
                "source": "Node1",
                "target": "Node2",
                "architype": "TestEdge",
            }
        ]

        get_graph, _, __ = EndpointFactory.create_endpoints(True, security)

        # Create FastAPI app and test client
        app = FastAPI()
        app.add_api_route("/graph", endpoint=get_graph, methods=["GET"])
        client = TestClient(app)

        # Send GET request with valid token
        response = client.get(
            "/graph",
            params={"root": "507f191e810c19729de860eb"},  # pragma: allowlist secret
            headers={"Authorization": "Bearer valid_token"},
        )

        # Verify response
        assert response.status_code == 200
        expected_response = {
            "nodes": [
                {
                    "id": "507f191e810c19729de860ea",  # pragma: allowlist secret
                    "data": "TestNode",
                    "name": "Node1",
                }
            ],
            "edges": [
                {
                    "id": "507f191e810c19729de860ec",  # pragma: allowlist secret
                    "name": "Edge1",
                    "source": "Node1",
                    "target": "Node2",
                    "data": "TestEdge",
                }
            ],
        }
        assert response.json() == expected_response

    def test_get_users_endpoint_auth(self, mocker: MockerFixture) -> None:
        """Test the /users endpoint with authentication."""
        security = HTTPBearer()

        # Mock database collections
        mock_get_collection = mocker.patch(
            "jvgraph.commands.launch.NodeAnchor.Collection.get_collection"
        )
        mock_user_collection = mocker.MagicMock()
        mock_get_collection.side_effect = lambda name: (
            mock_user_collection if name == "user" else None
        )

        # Mock decrypt function
        mock_decrypt = mocker.patch("jvgraph.commands.launch.decrypt")
        mock_decrypt.side_effect = [
            True,
        ]

        # Mock database response
        mock_user_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ed"),
                "root_id": "507f191e810c19729de860eb",
                "email": "user@example.com",
            }
        ]

        _, get_users, __ = EndpointFactory.create_endpoints(True, security)

        # Create FastAPI app and test client
        app = FastAPI()
        app.add_api_route("/users", endpoint=get_users, methods=["GET"])
        client = TestClient(app)

        # Send GET request with valid token
        response = client.get(
            "/users",
            headers={"Authorization": "Bearer valid_token"},
        )

        # Verify response
        assert response.status_code == 200
        expected_response = [
            {
                "id": "507f191e810c19729de860ed",  # pragma: allowlist secret
                "root_id": "507f191e810c19729de860eb",
                "email": "user@example.com",
            }
        ]
        assert response.json() == expected_response

    def test_get_node_endpoint_auth(self, mocker: MockerFixture) -> None:
        """Test the /graph/node endpoint with authentication."""
        security = HTTPBearer()

        # Mock database collections
        mock_get_collection = mocker.patch(
            "jvgraph.commands.launch.NodeAnchor.Collection.get_collection"
        )
        mock_node_collection = mocker.MagicMock()
        mock_edge_collection = mocker.MagicMock()
        mock_get_collection.side_effect = lambda name: (
            mock_node_collection if name == "node" else mock_edge_collection
        )

        # Mock decrypt function
        mock_decrypt = mocker.patch("jvgraph.commands.launch.decrypt")
        mock_decrypt.side_effect = [
            True,
        ]

        # Mock database responses for connected nodes
        mock_edge_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ec"),
                "source": "507f191e810c19729de860ea",  # pragma: allowlist secret
                "target": "507f191e810c19729de860ed",  # pragma: allowlist secret
                "name": "Edge1",
                "architype": "TestEdge",
            }
        ]

        mock_node_collection.find.return_value = [
            {
                "_id": ObjectId("507f191e810c19729de860ed"),
                "name": "Node2",
                "architype": "TestNode",
            }
        ]

        _, __, get_node = EndpointFactory.create_endpoints(True, security)

        # Create FastAPI app and test client
        app = FastAPI()
        app.add_api_route("/graph/node", endpoint=get_node, methods=["GET"])
        client = TestClient(app)

        # Send GET request with valid token
        response = client.get(
            "/graph/node",
            params={
                "node_id": "507f191e810c19729de860ea",  # pragma: allowlist secret
                "depth": 1,
            },
            headers={"Authorization": "Bearer valid_token"},
        )

        # Verify response
        assert response.status_code == 200
        expected_response = {
            "nodes": [
                {
                    "id": "507f191e810c19729de860ed",  # pragma: allowlist secret
                    "name": "Node2",
                    "data": "TestNode",
                }
            ],
            "edges": [
                {
                    "id": "507f191e810c19729de860ec",  # pragma: allowlist secret
                    "name": "Edge1",
                    "source": "507f191e810c19729de860ea",  # pragma: allowlist secret
                    "target": "507f191e810c19729de860ed",  # pragma: allowlist secret
                    "data": "TestEdge",
                }
            ],
        }
        assert response.json() == expected_response
