import from jvserve.cli { reload_jivas }

async walker exec_reload {

  class __specs__ {
    static has private: bool = True;  # Make this a private walker
  }

  can enter with entry {
    reload_jivas();
  }
}
