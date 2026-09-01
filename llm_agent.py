class LLMAttackAgent:

    def __init__(self, llm, executor, memory):
        self.llm = llm
        self.executor = executor
        self.memory = memory

    def run(self):

        while True:

            state = self.build_state()

            action = self.llm.generate_action(state)

            command = action["command"]

            output = self.executor.execute(command)

            self.memory.add(
                command,
                output
            )