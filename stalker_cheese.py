from unittest import case
from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from greedy_bot import *

class StalkerCheeseBot(BotAI):
    def __init__(self):
        self.nexus = None


    async def on_step(self, iteration: int):

        if(self.nexus == None):
            self.nexus = self.townhalls.ready.random 

        if(self.supply_used < 14 and self.nexus.is_idle):
            if self.can_afford(UnitTypeId.PROBE):
                await self.build(UnitTypeId.PROBE, near=self.nexus.position.towards(self.game_info.map_center, 5))
            return
        elif(self.supply_used == 14):
            builder_prob = self.units(UnitTypeId.PROBE).closest_to(self.nexus.position.towards(self.game_info.map_center, 5))
            if(self.already_pending(UnitTypeId.PYLON) == 0 and self.can_afford(UnitTypeId.PYLON)):
                await builder_prob.build(UnitTypeId.PYLON, near=self.nexus)
            return



run_game(maps.get("BlackburnAIE"), [
    Bot(Race.Protoss, StalkerCheeseBot(), name="Cheeser"),
    Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=True)