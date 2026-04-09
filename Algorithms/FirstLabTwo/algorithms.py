import math
import random
import time
from dataclasses import dataclass
from typing import Callable, List, Tuple


SEARCH_MIN = -10.0
SEARCH_MAX = 10.0
MIN_MUTATION_SCALE = 0.01
EPSILON = 1e-10


ObjectiveFn = Callable[[float, float], float]


def build_quadratic_objective(a: float, b: float, c: float) -> ObjectiveFn:
    def fn(x: float, y: float) -> float:
        return a * (x * x + y * y) + b * x * y + c

    return fn


@dataclass
class Candidate:
    x: float
    y: float
    value: float
    fitness: float = 0.0


class GeneticOptimizer:
    def __init__(
        self,
        objective: ObjectiveFn,
        population_size: int = 20,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.2,
        mutation_scale: float = 0.6,
        elite_fraction: float = 0.3,
        tournament_size: int = 3,
        use_new_population_mod: bool = True,
        seed: int = int(time.mktime(time.gmtime())),
    ) -> None:
        self.objective = objective
        self.population_size = population_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale
        self.elite_fraction = elite_fraction
        self.tournament_size = tournament_size
        self.use_new_population_mod = use_new_population_mod
        self._rng = random.Random(seed)
        self.iteration = 0
        self.population: List[Candidate] = []
        self.best_value = float("inf")
        self.best_iteration = 0
        self.reset()

    def set_objective(self, objective: ObjectiveFn) -> None:
        self.objective = objective
        for candidate in self.population:
            candidate.value = self.objective(candidate.x, candidate.y)
            candidate.fitness = 1.0 / (1.0 + abs(candidate.value))
        self.best_value = min((candidate.value for candidate in self.population), default=float("inf"))
        self.best_iteration = self.iteration

    def reset(self) -> None:
        self.iteration = 0
        self.population = []
        for _ in range(self.population_size):
            x = self._rng.uniform(SEARCH_MIN, SEARCH_MAX)
            y = self._rng.uniform(SEARCH_MIN, SEARCH_MAX)
            value = self.objective(x, y)
            self.population.append(Candidate(x=x, y=y, value=value, fitness=1.0 / (1.0 + abs(value))))
        self.best_value = min((candidate.value for candidate in self.population), default=float("inf"))
        self.best_iteration = 0

    def set_parameters(
        self,
        crossover_rate: float,
        mutation_rate: float,
        mutation_scale: float,
        elite_fraction: float,
        tournament_size: int,
        use_new_population_mod: bool,
    ) -> None:
        self.crossover_rate = max(0.0, min(1.0, crossover_rate))
        self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        self.mutation_scale = max(MIN_MUTATION_SCALE, mutation_scale)
        self.elite_fraction = max(0.0, min(0.9, elite_fraction))
        self.tournament_size = max(2, tournament_size)
        self.use_new_population_mod = use_new_population_mod

    def _select_parent(self) -> Candidate:
        k = min(self.tournament_size, len(self.population))
        pool = self._rng.sample(self.population, k)
        return min(pool, key=lambda item: item.value)

    def _crossover(self, p1: Candidate, p2: Candidate) -> Tuple[float, float]:
        if self._rng.random() < self.crossover_rate:
            w = self._rng.random()
            return w * p1.x + (1.0 - w) * p2.x, w * p1.y + (1.0 - w) * p2.y
        return p1.x, p1.y

    def _mutate(self, value: float) -> float:
        if self._rng.random() < self.mutation_rate:
            value += self._rng.gauss(0.0, self.mutation_scale)
        return min(SEARCH_MAX, max(SEARCH_MIN, value))

    def step(self) -> List[Tuple[int, float, float, float, float]]:
        self.population.sort(key=lambda item: item.value)
        if self.use_new_population_mod:
            elite_count = max(1, int(self.population_size * self.elite_fraction))
            next_generation: List[Candidate] = [
                Candidate(x=item.x, y=item.y, value=item.value, fitness=item.fitness)
                for item in self.population[:elite_count]
            ]

            while len(next_generation) < self.population_size:
                parent1 = self._select_parent()
                parent2 = self._select_parent()
                cx, cy = self._crossover(parent1, parent2)
                nx = self._mutate(cx)
                ny = self._mutate(cy)
                nv = self.objective(nx, ny)
                next_generation.append(Candidate(nx, ny, nv, fitness=1.0 / (1.0 + abs(nv))))

            next_generation.sort(key=lambda item: item.value)
            self.population = next_generation[: self.population_size]
        else:
            updated_population: List[Candidate] = []
            for candidate in self.population:
                partner = self._select_parent()
                cx, cy = self._crossover(candidate, partner)
                nx = self._mutate(cx)
                ny = self._mutate(cy)
                nv = self.objective(nx, ny)
                if nv < candidate.value:
                    updated_population.append(Candidate(nx, ny, nv, fitness=1.0 / (1.0 + abs(nv))))
                else:
                    updated_population.append(candidate)
            updated_population.sort(key=lambda item: item.value)
            self.population = updated_population
        self.iteration += 1
        current_best = min((candidate.value for candidate in self.population), default=float("inf"))
        if current_best < self.best_value:
            self.best_value = current_best
            self.best_iteration = self.iteration
        return [
            (idx + 1, candidate.x, candidate.y, candidate.value, candidate.fitness)
            for idx, candidate in enumerate(self.population)
        ]


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    best_x: float
    best_y: float
    best_value: float


class SwarmConstrictionOptimizer:
    def __init__(
        self,
        objective: ObjectiveFn,
        swarm_size: int = 20,
        c1: float = 2.05,
        c2: float = 2.05,
        inertia: float = 0.7,
        velocity_limit: float = 2.0,
        neighborhood_pull: float = 0.0,
        use_constriction_mod: bool = True,
        seed: int = int(time.mktime(time.gmtime())),
    ) -> None:
        self.objective = objective
        self.swarm_size = swarm_size
        self.c1 = c1
        self.c2 = c2
        self.inertia = inertia
        self.velocity_limit = velocity_limit
        self.neighborhood_pull = neighborhood_pull
        self.use_constriction_mod = use_constriction_mod
        self._rng = random.Random(seed)
        self.iteration = 0
        self.swarm: List[Particle] = []
        self.global_best: Tuple[float, float, float] = (0.0, 0.0, float("inf"))
        self.global_best_iteration = 0
        self.reset()

    def set_objective(self, objective: ObjectiveFn) -> None:
        self.objective = objective
        gx, gy, gvalue = 0.0, 0.0, float("inf")
        for particle in self.swarm:
            value = self.objective(particle.x, particle.y)
            particle.best_x = particle.x
            particle.best_y = particle.y
            particle.best_value = value
            if value < gvalue:
                gx, gy, gvalue = particle.x, particle.y, value
        self.global_best = (gx, gy, gvalue)
        self.global_best_iteration = self.iteration

    def _chi(self) -> float:
        phi = self.c1 + self.c2
        if phi <= 4.0:
            return 1.0
        radicand = phi * (phi - 4.0)
        sqrt_term = math.sqrt(radicand)
        denominator = abs(2.0 - phi - sqrt_term)
        return 2.0 / (denominator + EPSILON)

    def set_parameters(
        self,
        c1: float,
        c2: float,
        inertia: float,
        velocity_limit: float,
        neighborhood_pull: float,
        use_constriction_mod: bool,
    ) -> None:
        self.c1 = c1
        self.c2 = c2
        self.inertia = max(0.0, inertia)
        self.velocity_limit = max(0.01, velocity_limit)
        self.neighborhood_pull = max(0.0, neighborhood_pull)
        self.use_constriction_mod = use_constriction_mod

    def reset(self) -> None:
        self.iteration = 0
        self.swarm = []
        self.global_best = (0.0, 0.0, float("inf"))
        self.global_best_iteration = 0
        for _ in range(self.swarm_size):
            x = self._rng.uniform(SEARCH_MIN, SEARCH_MAX)
            y = self._rng.uniform(SEARCH_MIN, SEARCH_MAX)
            vx = self._rng.uniform(-1.0, 1.0)
            vy = self._rng.uniform(-1.0, 1.0)
            value = self.objective(x, y)
            p = Particle(x=x, y=y, vx=vx, vy=vy, best_x=x, best_y=y, best_value=value)
            self.swarm.append(p)
            if value < self.global_best[2]:
                self.global_best = (x, y, value)

    def step(self) -> List[Tuple[int, float, float, float, float, float]]:
        chi = self._chi() if self.use_constriction_mod else 1.0
        gx, gy, gvalue = self.global_best
        if self.neighborhood_pull > 0.0:
            cx = sum(p.x for p in self.swarm) / max(1, len(self.swarm))
            cy = sum(p.y for p in self.swarm) / max(1, len(self.swarm))
        else:
            cx = 0.0
            cy = 0.0
        rows: List[Tuple[int, float, float, float, float, float]] = []

        for idx, particle in enumerate(self.swarm):
            r1 = self._rng.random()
            r2 = self._rng.random()
            r3 = self._rng.random()
            particle.vx = chi * (
                self.inertia * particle.vx
                + self.c1 * r1 * (particle.best_x - particle.x)
                + self.c2 * r2 * (gx - particle.x)
                + self.neighborhood_pull * r3 * (cx - particle.x)
            )
            particle.vy = chi * (
                self.inertia * particle.vy
                + self.c1 * r1 * (particle.best_y - particle.y)
                + self.c2 * r2 * (gy - particle.y)
                + self.neighborhood_pull * r3 * (cy - particle.y)
            )

            particle.vx = max(-self.velocity_limit, min(self.velocity_limit, particle.vx))
            particle.vy = max(-self.velocity_limit, min(self.velocity_limit, particle.vy))
            particle.x = min(SEARCH_MAX, max(SEARCH_MIN, particle.x + particle.vx))
            particle.y = min(SEARCH_MAX, max(SEARCH_MIN, particle.y + particle.vy))

            value = self.objective(particle.x, particle.y)
            if value < particle.best_value:
                particle.best_x = particle.x
                particle.best_y = particle.y
                particle.best_value = value
            if value < gvalue:
                gx, gy, gvalue = particle.x, particle.y, value
                self.global_best_iteration = self.iteration + 1

            rows.append((idx + 1, particle.x, particle.y, value, particle.vx, particle.vy))

        self.global_best = (gx, gy, gvalue)
        self.iteration += 1
        return rows
