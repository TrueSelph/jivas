import from jivas.agent.action.agent_graph_walker { agent_graph_walker }
import from jivas.agent.core.agent { Agent }
import from jivas.agent.action.action { Action }
import from jivas.agent.action.actions { Actions }

walker export_descriptor(agent_graph_walker) {
    # accepts agent_id and returns dict / yaml of exported agent descriptor

    has as_yaml: bool = False;
    has clean:bool = False;

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        report here.get_descriptor(as_yaml=self.as_yaml, clean=self.clean);
    }
}