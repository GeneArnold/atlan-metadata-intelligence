"""
Databricks Genie Conversation API Client.

This module provides a Python wrapper for calling Databricks Genie API
to query data using natural language.
"""

import httpx
import time
from typing import Dict, List, Any, Optional, Tuple
import json


class GenieClient:
    """Client for interacting with Databricks Genie Conversation API."""

    def __init__(self, workspace_url: str, token: str, space_id: str):
        """
        Initialize the Genie client.

        Args:
            workspace_url: Databricks workspace URL (e.g., https://your-workspace.cloud.databricks.com)
            token: Databricks personal access token
            space_id: Genie space ID
        """
        self.workspace_url = workspace_url.rstrip("/")
        self.token = token
        self.space_id = space_id
        self.api_base = f"{self.workspace_url}/api/2.0/genie"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def start_conversation(self, question: str) -> Tuple[str, str]:
        """
        Start a new conversation with a question.

        Args:
            question: Natural language question to ask

        Returns:
            Tuple of (conversation_id, message_id)
        """
        url = f"{self.api_base}/spaces/{self.space_id}/start-conversation"
        payload = {"content": question}

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            return data["conversation_id"], data["message_id"]

    def continue_conversation(self, conversation_id: str, question: str) -> str:
        """
        Continue an existing conversation with a follow-up question.

        Args:
            conversation_id: Existing conversation ID
            question: Follow-up question

        Returns:
            message_id for the new message
        """
        url = f"{self.api_base}/spaces/{self.space_id}/conversations/{conversation_id}/messages"
        payload = {"content": question}

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            return data["message_id"]

    def get_message_status(
        self, conversation_id: str, message_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of a message.

        Args:
            conversation_id: Conversation ID
            message_id: Message ID

        Returns:
            Message status dictionary with status, attachments, etc.
        """
        url = f"{self.api_base}/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    def get_query_result(
        self, conversation_id: str, message_id: str, attachment_id: str
    ) -> Dict[str, Any]:
        """
        Get query results from an attachment.

        Args:
            conversation_id: Conversation ID
            message_id: Message ID
            attachment_id: Attachment ID containing query results

        Returns:
            Query results dictionary
        """
        url = f"{self.api_base}/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}"

        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    def generate_sql_only(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        max_wait_seconds: int = 300,
        poll_interval: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Ask a question and get the generated SQL WITHOUT executing it.
        This enables governance checks before query execution.

        Args:
            question: Natural language question to ask
            conversation_id: Optional existing conversation ID to continue (None = start new)
            max_wait_seconds: Maximum time to wait for SQL generation (default: 5 minutes)
            poll_interval: Initial polling interval in seconds (default: 2s)

        Returns:
            Dictionary containing:
                - status: "completed", "failed", or "timeout"
                - conversation_id: Conversation ID
                - message_id: Message ID
                - attachment_id: Attachment ID (needed to execute query later)
                - text_response: Text response from Genie (if available)
                - sql_query: Generated SQL query (NOT executed)
                - error: Error message (if failed)
        """
        result = {
            "status": "unknown",
            "conversation_id": None,
            "message_id": None,
            "attachment_id": None,
            "text_response": None,
            "sql_query": None,
            "error": None,
        }

        try:
            # Start new conversation or continue existing one
            if conversation_id is None:
                # Start new conversation
                conversation_id, message_id = self.start_conversation(question)
            else:
                # Continue existing conversation
                message_id = self.continue_conversation(conversation_id, question)

            result["conversation_id"] = conversation_id
            result["message_id"] = message_id

            # Poll for completion
            start_time = time.time()
            current_poll_interval = poll_interval

            while time.time() - start_time < max_wait_seconds:
                # Get message status
                message_data = self.get_message_status(conversation_id, message_id)
                status = message_data.get("status", "UNKNOWN")

                if status == "COMPLETED":
                    result["status"] = "completed"

                    # Extract attachments - SQL and text response
                    attachments = message_data.get("attachments", [])
                    for attachment in attachments:
                        # Get text response (Genie's answer)
                        if "text" in attachment and "content" in attachment["text"]:
                            result["text_response"] = attachment["text"]["content"]

                        # Get query attachment (SQL) - BUT DON'T EXECUTE
                        if attachment.get("query"):
                            query_obj = attachment["query"]
                            result["sql_query"] = query_obj.get("query")

                            # Save attachment_id for later execution
                            attachment_id = attachment.get("attachment_id")
                            if attachment_id:
                                result["attachment_id"] = attachment_id

                    return result

                elif status == "FAILED" or status == "CANCELLED":
                    result["status"] = "failed"
                    result["error"] = f"Message status: {status}"
                    return result

                # Exponential backoff (up to 10 seconds)
                time.sleep(current_poll_interval)
                current_poll_interval = min(current_poll_interval * 1.5, 10.0)

            # Timeout
            result["status"] = "timeout"
            result["error"] = f"Request timed out after {max_wait_seconds} seconds"
            return result

        except httpx.HTTPError as e:
            result["status"] = "failed"
            result["error"] = f"HTTP error: {str(e)}"
            return result
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"Unexpected error: {str(e)}"
            return result

    def execute_query(
        self,
        conversation_id: str,
        message_id: str,
        attachment_id: str,
    ) -> Dict[str, Any]:
        """
        Execute a previously generated query (after governance checks pass).

        Args:
            conversation_id: Conversation ID
            message_id: Message ID
            attachment_id: Attachment ID from generate_sql_only()

        Returns:
            Dictionary containing query results
        """
        try:
            query_result = self.get_query_result(
                conversation_id, message_id, attachment_id
            )
            return {"status": "completed", "query_results": query_result}
        except Exception as e:
            return {"status": "failed", "error": f"Error executing query: {str(e)}"}

    def ask_question(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        max_wait_seconds: int = 300,
        poll_interval: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Ask a question and wait for the complete response.

        Args:
            question: Natural language question to ask
            conversation_id: Optional existing conversation ID to continue (None = start new)
            max_wait_seconds: Maximum time to wait for response (default: 5 minutes)
            poll_interval: Initial polling interval in seconds (default: 2s)

        Returns:
            Dictionary containing:
                - status: "completed", "failed", or "timeout"
                - conversation_id: Conversation ID
                - message_id: Message ID
                - text_response: Text response from Genie (if available)
                - sql_query: Generated SQL query (if available)
                - query_results: Query results data (if available)
                - error: Error message (if failed)
        """
        result = {
            "status": "unknown",
            "conversation_id": None,
            "message_id": None,
            "text_response": None,
            "sql_query": None,
            "query_results": None,
            "error": None,
        }

        try:
            # Start new conversation or continue existing one
            if conversation_id is None:
                # Start new conversation
                conversation_id, message_id = self.start_conversation(question)
            else:
                # Continue existing conversation
                message_id = self.continue_conversation(conversation_id, question)

            result["conversation_id"] = conversation_id
            result["message_id"] = message_id

            # Poll for completion
            start_time = time.time()
            current_poll_interval = poll_interval

            while time.time() - start_time < max_wait_seconds:
                # Get message status
                message_data = self.get_message_status(conversation_id, message_id)
                status = message_data.get("status", "UNKNOWN")

                if status == "COMPLETED":
                    result["status"] = "completed"

                    # Extract attachments first
                    # Genie's text response is in attachments[].text.content!
                    attachments = message_data.get("attachments", [])
                    for attachment in attachments:
                        # Get text response (Genie's answer)
                        if "text" in attachment and "content" in attachment["text"]:
                            result["text_response"] = attachment["text"]["content"]

                        # Get query attachment (SQL)
                        if attachment.get("query"):
                            query_obj = attachment["query"]
                            result["sql_query"] = query_obj.get("query")

                            # Get query results if available - attachment_id is at attachment level, not inside query
                            attachment_id = attachment.get("attachment_id")
                            if attachment_id:
                                try:
                                    query_result = self.get_query_result(
                                        conversation_id, message_id, attachment_id
                                    )
                                    result["query_results"] = query_result
                                except Exception as e:
                                    result["error"] = f"Error fetching query results: {str(e)}"

                    return result

                elif status == "FAILED" or status == "CANCELLED":
                    result["status"] = "failed"
                    result["error"] = f"Message status: {status}"
                    return result

                # Exponential backoff (up to 10 seconds)
                time.sleep(current_poll_interval)
                current_poll_interval = min(current_poll_interval * 1.5, 10.0)

            # Timeout
            result["status"] = "timeout"
            result["error"] = f"Request timed out after {max_wait_seconds} seconds"
            return result

        except httpx.HTTPError as e:
            result["status"] = "failed"
            result["error"] = f"HTTP error: {str(e)}"
            return result
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"Unexpected error: {str(e)}"
            return result

    def list_spaces(self) -> List[Dict[str, Any]]:
        """
        List all Genie spaces.

        Returns:
            List of Genie space dictionaries
        """
        url = f"{self.api_base}/spaces"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
