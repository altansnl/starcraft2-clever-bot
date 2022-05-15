from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI

class GreedyBot(BotAI):
    async def on_step(self, iteration: int):
        print(f"This is my bot in iteration {iteration}!")

run_game(maps.get("BlackburnAIE"), [
    Bot(Race.Protoss, GreedyBot()),
    Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=True)
