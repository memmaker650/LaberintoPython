import pygame
import math
import random

# =======================
# COMPONENTE: SALUD
# =======================
class Salud:
    def __init__(self, vida_max):
        self.vida = vida_max
        self.vida_max = vida_max
        self.invulnerable = False
        self.tiempo_invulnerable = 0

    def daño(self, cantidad, tiempo_actual):
        if not self.invulnerable and self.vida > 0:
            self.vida = max(0, self.vida - cantidad)
            self.invulnerable = True
            self.tiempo_invulnerable = tiempo_actual + 1000  # 1s invulnerable
            print(f"💥 Enemigo recibe {cantidad} daño. Vida = {self.vida}")
            return True
        return False

    def update(self, tiempo_actual):
        if self.invulnerable and tiempo_actual > self.tiempo_invulnerable:
            self.invulnerable = False

    def porcentaje_vida(self):
        return self.vida / self.vida_max


# =======================
# COMPONENTES DE IA
# =======================
class InteligenciaBase:
    def mover(self, enemigo, jugador_pos):
        pass


class InteligenciaPasiva(InteligenciaBase):
    def mover(self, enemigo, jugador_pos):
        enemigo.x += random.choice([-1, 0, 1])
        enemigo.y += random.choice([-1, 0, 1])


class InteligenciaAgresiva(InteligenciaBase):
    def mover(self, enemigo, jugador_pos):
        dx = jugador_pos[0] - enemigo.x
        dy = jugador_pos[1] - enemigo.y
        distancia = math.hypot(dx, dy)
        if distancia > 0:
            enemigo.x += enemigo.velocidad_agresiva * dx / distancia
            enemigo.y += enemigo.velocidad_agresiva * dy / distancia


# =======================
# COMPONENTE: SONIDO
# =======================
class Sonido:
    def __init__(self):
        self.reproduciendo = False

    def reproducir_alerta(self):
        if not self.reproduciendo:
            print("🔊 ALERTA activada")
            self.reproduciendo = True

    def detener_alerta(self):
        if self.reproduciendo:
            print("🔇 ALERTA detenida")
            self.reproduciendo = False


# =======================
# COMPONENTE: LOOT (Botín)
# =======================
class Loot(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo):
        super().__init__()
        self.tipo = tipo
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)

        colores = {
            "moneda": (255, 215, 0),    # dorado
            "pocion": (0, 255, 255),    # cian
            "gema": (255, 0, 255)       # magenta
        }
        self.image.fill(colores.get(tipo, (255, 255, 255)))
        self.rect = self.image.get_rect(center=(x, y))

        # Efecto de flotación visual
        self.tiempo_nacimiento = pygame.time.get_ticks()
        self.offset_y = 0

    def update(self):
        # Hace que el loot flote suavemente
        t = (pygame.time.get_ticks() - self.tiempo_nacimiento) / 500
        self.offset_y = math.sin(t) * 5
        self.rect.y += self.offset_y


class LootSystem:
    """Sistema que gestiona qué botín suelta un enemigo al morir"""
    TIPOS_POSSIBLES = ["moneda", "pocion", "gema"]

    @staticmethod
    def generar(x, y, grupo_loot):
        if random.random() < 0.75:  # 75% de probabilidad de soltar algo
            tipo = random.choice(LootSystem.TIPOS_POSSIBLES)
            loot = Loot(x, y, tipo)
            grupo_loot.add(loot)
            print(f"🎁 Enemigo soltó: {tipo}")


# =======================
# CLASE ENEMIGO (Composición)
# =======================
class Enemigo(pygame.sprite.Sprite):
    def __init__(self, x, y, grupo_loot):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.x, self.y = x, y

        # Componentes
        self.salud = Salud(100)
        self.ia_pasiva = InteligenciaPasiva()
        self.ia_agresiva = InteligenciaAgresiva()
        self.ia = self.ia_pasiva
        self.sonido = Sonido()
        self.grupo_loot = grupo_loot

        # Parámetros
        self.radio_alerta = 150
        self.velocidad_agresiva = 3
        self.color_pasivo = (255, 0, 0)
        self.color_agresivo = (255, 140, 0)
        self.color_danio = (255, 255, 255)
        self.color_barra_vida = (0, 255, 0)
        self.color_barra_fondo = (60, 60, 60)

        # Estados
        self.agresivo = False
        self.atacado = False
        self.tiempo_recuperacion = 0
        self.velocidad_actual = 1
        self.vivo = True
        self.transparencia = 255

    def update(self, jugador_pos, tiempo_actual):
        self.salud.update(tiempo_actual)

        if not self.vivo:
            self.transparencia -= 5
            if self.transparencia <= 0:
                self.kill()
            self.image.set_alpha(self.transparencia)
            return

        dx = jugador_pos[0] - self.x
        dy = jugador_pos[1] - self.y
        distancia = math.hypot(dx, dy)

        if distancia < self.radio_alerta and not self.agresivo:
            self.cambiar_a_agresivo()
        elif distancia >= self.radio_alerta and self.agresivo:
            self.cambiar_a_pasivo()

        if self.atacado and tiempo_actual > self.tiempo_recuperacion:
            self.atacado = False
            self.velocidad_actual = 1
            self.actualizar_color()

        self.ia.mover(self, jugador_pos)
        self.rect.center = (self.x, self.y)

        if self.salud.vida <= 0:
            self.morir()

    def cambiar_a_agresivo(self):
        self.ia = self.ia_agresiva
        self.agresivo = True
        self.actualizar_color()
        self.sonido.reproducir_alerta()

    def cambiar_a_pasivo(self):
        self.ia = self.ia_pasiva
        self.agresivo = False
        self.actualizar_color()
        self.sonido.detener_alerta()

    def actualizar_color(self):
        if self.atacado:
            self.image.fill(self.color_danio)
        elif self.agresivo:
            self.image.fill(self.color_agresivo)
        else:
            self.image.fill(self.color_pasivo)

    def recibir_danio(self, cantidad, tiempo_actual):
        golpe = self.salud.daño(cantidad, tiempo_actual)
        if golpe:
            self.atacado = True
            self.velocidad_actual = 0.3
            self.tiempo_recuperacion = tiempo_actual + 1500
            self.actualizar_color()

    def morir(self):
        if self.vivo:
            self.vivo = False
            print("💀 Enemigo derrotado")
            LootSystem.generar(self.x, self.y, self.grupo_loot)

    def dibujar_barra_vida(self, superficie):
        if not self.vivo:
            return
        ancho, alto = self.rect.width, 5
        porcentaje = self.salud.porcentaje_vida()
        x = self.rect.centerx - ancho // 2
        y = self.rect.top - 10
        pygame.draw.rect(superficie, self.color_barra_fondo, (x, y, ancho, alto))
        pygame.draw.rect(superficie, self.color_barra_vida, (x, y, ancho * porcentaje, alto))


# =======================
# BUCLE PRINCIPAL
# =======================
def main():
    pygame.init()
    pantalla = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Enemigo con Loot")
    clock = pygame.time.Clock()

    jugador_pos = [300, 200]
    enemigos = pygame.sprite.Group()
    loot_group = pygame.sprite.Group()
    enemigo = Enemigo(200, 150, loot_group)
    enemigos.add(enemigo)

    jugando = True
    while jugando:
        tiempo_actual = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                jugando = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                enemigo.recibir_danio(25, tiempo_actual)

        jugador_pos = pygame.mouse.get_pos()

        enemigos.update(jugador_pos, tiempo_actual)
        loot_group.update()

        pantalla.fill((30, 30, 30))
        pygame.draw.circle(pantalla, (0, 255, 0), jugador_pos, 10)
        enemigos.draw(pantalla)
        loot_group.draw(pantalla)

        for en in enemigos:
            en.dibujar_barra_vida(pantalla)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
