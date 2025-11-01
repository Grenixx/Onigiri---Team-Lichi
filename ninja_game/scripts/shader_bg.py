import moderngl
import numpy as np
import pygame
import time

class ShaderBackground:
    def __init__(self, width, height, frag_shader_path):
        self.width = width
        self.height = height
        self.start_time = time.time()

        # Contexte OpenGL offscreen (ne remplace pas ta fenêtre pygame)
        self.ctx = moderngl.create_standalone_context()

        with open(frag_shader_path, "r") as f:
            frag_src = f.read()

        # Programme OpenGL
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }
            """,
            fragment_shader=frag_src
        )

        # Quad plein écran
        self.vbo = self.ctx.buffer(np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype='f4').tobytes())

        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert')

        # Framebuffer pour dessiner dans une texture
        self.fbo = self.ctx.simple_framebuffer((width, height))
        self.fbo.use()

    def render(self):
        """Renvoie un pygame.Surface contenant le shader rendu"""
        self.fbo.clear()
        self.prog["u_time"] = time.time() - self.start_time
        self.prog["u_resolution"] = (self.width, self.height)

        self.vao.render(moderngl.TRIANGLE_STRIP)
        data = self.fbo.read(components=3)
        image = pygame.image.frombuffer(data, (self.width, self.height), "RGB")
        return pygame.transform.flip(image, False, True)
