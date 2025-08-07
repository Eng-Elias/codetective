"""
LangGraph workflow graph builder for codetective.
"""

from typing import Dict, Any, List, Callable
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from codetective.models.workflow_state import WorkflowState
from codetective.utils.logger import Logger


class GraphBuilder:
    """
    Builder class for constructing LangGraph workflow graphs.
    
    This class provides utilities for building complex workflow graphs
    with conditional routing, parallel execution, and error handling.
    """
    
    def __init__(self):
        """Initialize the graph builder."""
        self.logger = Logger.get_logger("workflow.graph_builder")
        self.graph = None
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}
    
    def create_workflow_graph(self) -> StateGraph:
        """
        Create a new workflow graph.
        
        Returns:
            StateGraph instance for building workflows
        """
        self.graph = StateGraph(WorkflowState)
        self.logger.info("Created new workflow graph")
        return self.graph
    
    def add_analysis_node(
        self,
        name: str,
        node_function: Callable,
        description: str = ""
    ) -> "GraphBuilder":
        """
        Add an analysis node to the graph.
        
        Args:
            name: Node name
            node_function: Function to execute for this node
            description: Optional description
            
        Returns:
            Self for method chaining
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call create_workflow_graph() first.")
        
        self.graph.add_node(name, node_function)
        self.nodes[name] = {
            "function": node_function,
            "description": description,
            "type": "analysis"
        }
        
        self.logger.debug(f"Added analysis node: {name}")
        return self
    
    def add_control_node(
        self,
        name: str,
        node_function: Callable,
        description: str = ""
    ) -> "GraphBuilder":
        """
        Add a control flow node to the graph.
        
        Args:
            name: Node name
            node_function: Function to execute for this node
            description: Optional description
            
        Returns:
            Self for method chaining
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call create_workflow_graph() first.")
        
        self.graph.add_node(name, node_function)
        self.nodes[name] = {
            "function": node_function,
            "description": description,
            "type": "control"
        }
        
        self.logger.debug(f"Added control node: {name}")
        return self
    
    def add_simple_edge(self, from_node: str, to_node: str) -> "GraphBuilder":
        """
        Add a simple edge between two nodes.
        
        Args:
            from_node: Source node name
            to_node: Target node name
            
        Returns:
            Self for method chaining
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call create_workflow_graph() first.")
        
        self.graph.add_edge(from_node, to_node)
        
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        
        self.logger.debug(f"Added edge: {from_node} -> {to_node}")
        return self
    
    def add_conditional_edge(
        self,
        from_node: str,
        condition_function: Callable,
        edge_mapping: Dict[str, str]
    ) -> "GraphBuilder":
        """
        Add a conditional edge with routing logic.
        
        Args:
            from_node: Source node name
            condition_function: Function that returns routing key
            edge_mapping: Mapping of routing keys to target nodes
            
        Returns:
            Self for method chaining
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call create_workflow_graph() first.")
        
        self.graph.add_conditional_edges(
            from_node,
            condition_function,
            edge_mapping
        )
        
        self.conditional_edges[from_node] = {
            "condition": condition_function,
            "mapping": edge_mapping
        }
        
        self.logger.debug(f"Added conditional edge from {from_node} with {len(edge_mapping)} routes")
        return self
    
    def set_entry_point(self, node_name: str) -> "GraphBuilder":
        """
        Set the entry point for the workflow.
        
        Args:
            node_name: Name of the entry node
            
        Returns:
            Self for method chaining
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call create_workflow_graph() first.")
        
        self.graph.set_entry_point(node_name)
        self.logger.debug(f"Set entry point: {node_name}")
        return self
    
    def compile_graph(self) -> CompiledStateGraph:
        """
        Compile the graph for execution.
        
        Returns:
            Compiled graph ready for execution
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call create_workflow_graph() first.")
        
        try:
            compiled_graph = self.graph.compile()
            self.logger.info("Graph compiled successfully")
            return compiled_graph
        
        except Exception as e:
            self.logger.error(f"Graph compilation failed: {e}")
            raise
    
    def validate_graph(self) -> List[str]:
        """
        Validate the graph structure.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.graph:
            errors.append("Graph not initialized")
            return errors
        
        # Check for orphaned nodes
        all_nodes = set(self.nodes.keys())
        referenced_nodes = set()
        
        # Add nodes referenced in simple edges
        for from_node, to_nodes in self.edges.items():
            referenced_nodes.add(from_node)
            referenced_nodes.update(to_nodes)
        
        # Add nodes referenced in conditional edges
        for from_node, edge_info in self.conditional_edges.items():
            referenced_nodes.add(from_node)
            referenced_nodes.update(edge_info["mapping"].values())
        
        orphaned_nodes = all_nodes - referenced_nodes
        if orphaned_nodes:
            errors.append(f"Orphaned nodes found: {orphaned_nodes}")
        
        # Check for missing node references
        missing_nodes = referenced_nodes - all_nodes
        if missing_nodes:
            errors.append(f"Referenced nodes not defined: {missing_nodes}")
        
        return errors
    
    def get_graph_info(self) -> Dict[str, Any]:
        """
        Get information about the current graph.
        
        Returns:
            Dictionary with graph information
        """
        return {
            "nodes": list(self.nodes.keys()),
            "node_count": len(self.nodes),
            "simple_edges": self.edges,
            "conditional_edges": list(self.conditional_edges.keys()),
            "analysis_nodes": [name for name, info in self.nodes.items() if info["type"] == "analysis"],
            "control_nodes": [name for name, info in self.nodes.items() if info["type"] == "control"],
        }
    
    def visualize_graph(self) -> str:
        """
        Create a text representation of the graph.
        
        Returns:
            Text visualization of the graph structure
        """
        lines = ["Graph Structure:", "=" * 15]
        
        # Show nodes
        lines.append("\nNodes:")
        for name, info in self.nodes.items():
            lines.append(f"  • {name} ({info['type']})")
            if info["description"]:
                lines.append(f"    {info['description']}")
        
        # Show simple edges
        if self.edges:
            lines.append("\nSimple Edges:")
            for from_node, to_nodes in self.edges.items():
                for to_node in to_nodes:
                    lines.append(f"  {from_node} → {to_node}")
        
        # Show conditional edges
        if self.conditional_edges:
            lines.append("\nConditional Edges:")
            for from_node, edge_info in self.conditional_edges.items():
                lines.append(f"  {from_node} → [conditional]")
                for condition, to_node in edge_info["mapping"].items():
                    lines.append(f"    {condition}: {to_node}")
        
        return "\n".join(lines)


def create_standard_workflow_graph() -> CompiledStateGraph:
    """
    Create a standard workflow graph for multi-agent analysis.
    
    Returns:
        Compiled graph ready for execution
    """
    builder = GraphBuilder()
    
    # This would be implemented with actual node functions
    # For now, return None as a placeholder
    return None
