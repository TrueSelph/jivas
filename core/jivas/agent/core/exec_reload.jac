import time;
import from jvserve.cli { reload_jivas }

async walker exec_reload {

  class __specs__ {
    static has private: bool = False;
  }

  can enter with entry {
    time.sleep(3);
    reload_jivas();
  }
}
