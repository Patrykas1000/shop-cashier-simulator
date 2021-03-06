import arcade
from typing import *
import enum
from game.Utils import DraggableList, resourcePath, currTimeMs, noProducts
import game.GameObjects as go
import random
import pyglet.gl as gl


class LoseReason(enum.Enum):
    PRODUCT_MISSED = "Nie skasowano wszystkich produktów"
    WRONG_NUMBER_OF_PRODUCTS = "Wprowadzono złą liczbe produktów"

class GameView(arcade.View):

    def __init__(self):
        from game.Utils import resourcePath
        super().__init__()
        self.productByPieceList = [
            go.Product("Pepti",    go.ProductType.BY_PIECE, 200, resourcePath("Products/pepti.png"),     0, 0, 100, 100),
            go.Product("KavaJawa", go.ProductType.BY_PIECE, 700, resourcePath("Products/kava_jawa.png"), 0, 0, 100, 100),
            go.Product("Sok",      go.ProductType.BY_PIECE, 150, resourcePath("Products/juice.png"),     0, 0, 100, 100),
            go.Product("Lipzon",   go.ProductType.BY_PIECE, 600, resourcePath("Products/lipzon.png"),    0, 0, 100, 100),
            go.Product("Pizza",    go.ProductType.BY_PIECE, 950, resourcePath("Products/pizza.png"),     0, 0, 100, 100),
            go.Product("Chleb",    go.ProductType.BY_PIECE, 950, resourcePath("Products/bread.png"),     0, 0, 100, 100),
            go.Product("Tort",     go.ProductType.BY_PIECE, 750, resourcePath("Products/cake.png"),      0, 0, 100, 100),
        ]
        self.productByWeightList = [
            go.Product("Jabłko",    go.ProductType.BY_WEIGHT, 100, resourcePath("Products/apple.png"),    0, 0, 100, 100),
            go.Product("Brokół",    go.ProductType.BY_WEIGHT, 50 , resourcePath("Products/broccoli.png"), 0, 0, 100, 100),
            go.Product("Banan",     go.ProductType.BY_WEIGHT, 500, resourcePath("Products/banana.png"),   0, 0, 100, 100),
            go.Product("Marchew",   go.ProductType.BY_WEIGHT, 100, resourcePath("Products/carrot.png"),   0, 0, 100, 100),
            go.Product("Wisnia",    go.ProductType.BY_WEIGHT, 250, resourcePath("Products/cherry.png"),   0, 0, 100, 100),
            go.Product("Kukurydza", go.ProductType.BY_WEIGHT, 250, resourcePath("Products/corn.png"),     0, 0, 100, 100),
            go.Product("Cebula",    go.ProductType.BY_WEIGHT, 50 , resourcePath("Products/onion.png"),    0, 0, 100, 100),
            go.Product("Ziemniak",  go.ProductType.BY_WEIGHT, 50 , resourcePath("Products/potato.png"),   0, 0, 100, 100),
        ]


        self.gameObjects = [] #arcade.SpriteList()


        self.draggableList = DraggableList(self.gameObjects)
        self.draggableList.reverse() # Makes sprites at top the most priority
        self.scanner = arcade.Sprite(resourcePath("UI/scanner.png"), scale=0.25, center_x=400, center_y=150)
        self.cashRegister = go.CashRegister(400, 400,
                                         onScan=self.onScan,
                                         onNext=self.nextClient,
                                         onOk=self.onOkButton
                                        )
        self.currentProducts = {}
        self.checkedProducts = {}
        self.times = []
        self.currClientStartTime = 0
        self.noClients = 0


    def endGame(self, reason :LoseReason):
        """Moves to GameEndView
        :param reason: reason of lose
        """
        self.window.show_view(GameEndView(reason, self.noClients, self.times))

    # ======== Callbacks ========
    def onScan(self):
        col = []
        for obj in self.gameObjects:
            if self.scanner.collides_with_sprite(obj):
                col.append(obj)

        return col

    def onOkButton(self, product :Union[go.Product, List[go.Product]], count :int):
        if isinstance(product, go.Product):
            self.flagAsChecked(product, count)
        else:
            for prd in product:
                self.flagAsChecked(prd, 1)

    def nextClient(self):
        """Prepares view for next client, do checks, removes old items, and setup new
        """
        noChecked = noProducts(self.checkedProducts)
        noCurrent = noProducts(self.currentProducts)
        if self.noClients == 0 or noChecked == noCurrent:
            self.checkedProducts.clear()
            self.currentProducts = self.generateClient()
            self.gameObjects = []  # arcade.SpriteList()
            for product in self.currentProducts.keys():
                if product.getType() == go.ProductType.BY_PIECE:
                    for i in range(self.currentProducts[product]):
                        self.addProductAsGameObject(product.clone())
                else:
                    self.addProductAsGameObject(product)

            self.draggableList = DraggableList(self.gameObjects)
            self.draggableList.reverse()  # Makes sprites at top the most priority

            currTime = currTimeMs()
            if self.currClientStartTime != 0:
                self.times.append(currTime - self.currClientStartTime)
            self.currClientStartTime = currTime
            self.noClients += 1
        else:
            self.endGame(LoseReason.PRODUCT_MISSED)

    # ======== Game functions ========

    def addProductAsGameObject(self, product :go.Product):
        product.center_x = random.randint(550, 750)
        product.center_y = random.randint(50, 550)
        self.gameObjects.append(product)


    def flagAsChecked(self, product :go.Product, count :int):
        """Flags specific product as checked witch means product was scanned and scan was accepted by pressing "ok"
        button.

        :param product: Product to flag
        :param count: Number of products of same kind (equal by __eq__ func)
        """
        if product in self.currentProducts:
            currCount = self.currentProducts[product]
            if product in self.checkedProducts:
                currCount -= self.checkedProducts[product]

            if currCount - count >= 0:
                if product in self.checkedProducts:
                    self.checkedProducts[product] += count
                else:
                    self.checkedProducts[product] = count
            else:
                self.endGame(LoseReason.WRONG_NUMBER_OF_PRODUCTS)


    def generateClient(self) -> Dict[go.Product, int]:
        """Creates client product dictionary
        :return: Client product dictionary
        """
        minProductCount = 10
        maxProductCount = 20
        minProductWeight = 0.05
        maxProductWeight = 2
        products = {}
        n = random.randint(minProductCount, maxProductCount)

        for i in range(n):
            # half of products are by_weight
            randomProduct = random.choice( self.productByWeightList if i < n/2 else self.productByPieceList )

            randWeight = random.random()*(maxProductWeight - minProductWeight) + minProductWeight
            randomProduct = randomProduct.clone( int(randWeight*100_00)//100 if randomProduct.getType() == go.ProductType.BY_WEIGHT else -1 )
            if randomProduct in products:
                products[randomProduct] += 1
            else:
                products[randomProduct] = 1


        return products

    def on_show(self):
        arcade.set_background_color(arcade.color.ALICE_BLUE)


    def on_draw(self):
        arcade.start_render()
        # Pixel perfect settings (in OpenGL)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        self.cashRegister.draw()
        self.scanner.draw()
        for obj in self.gameObjects:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            obj.draw()
        #self.gameObjects.draw()

        pass

    def on_update(self, delta_time: float):
        for obj in self.gameObjects:
            obj.update()
        #self.gameObjects.update()
        pass

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.draggableList.dragStart(x, y)
            self.cashRegister.onMousePress(x, y)


    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.draggableList.dragStop()
            self.cashRegister.onMouseRelease(x, y)


    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, _buttons: int, _modifiers: int):
        if _buttons & arcade.MOUSE_BUTTON_LEFT == arcade.MOUSE_BUTTON_LEFT:
            self.draggableList.drag(x, y, dx, dy)


    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.cashRegister.onMouseMove(x, y, dx, dy)

class MenuView(arcade.View):

    def __init__(self):
        super().__init__()

        self.theme = arcade.Theme()
        self.sprites = arcade.SpriteList()

    def startGame(self):
        self.window.show_view(GameView())

    def exitGame(self):
        self.window.close()

    def setupTheme(self):
        self.theme.set_font(18, arcade.color.BLACK, resourcePath("Fonts/PS2P.ttf"))
        normal = resourcePath("UI/menuButton.png")
        hover = resourcePath("UI/menuButton_hover.png")
        clicked = resourcePath("UI/menuButton_clicked.png")
        locked = resourcePath("UI/menuButton_locked.png")
        self.theme.add_button_textures(normal, hover, clicked, locked)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

        self.setupTheme()

        (w, h) = self.window.get_size()

        self.button_list.append(go.ActionButton(150, h-75,  200, 50, "Start",   self.theme, action=lambda source: self.startGame()))
        self.button_list.append(go.ActionButton(150, h-150, 200, 50, "Wyjście", self.theme, action=lambda source: self.exitGame() ))

        backgroundImage = arcade.Sprite(resourcePath("UI/menuBg.png"), 4, 0, 0, 0, 0, w/2, h/2)
        self.sprites.append(backgroundImage)

    def on_draw(self):
        arcade.start_render()

        # Pixel perfect settings (in OpenGL)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)


        self.sprites.draw( filter=gl.GL_NEAREST )

        for button in self.button_list:
            button.draw()



def drawText(text, x, y, size):
    arcade.draw_text(text, x, y, arcade.color.BLACK, size, 0,
                     align="center", anchor_x="center", anchor_y="top",
                     font_name=resourcePath("Fonts/PS2P.ttf")
                    )

class GameEndView(arcade.View):


    def __init__(self, loseReason :LoseReason, noClients :int, times :List[int]):
        super().__init__()
        self.__loseReason = loseReason
        self.__text = loseReason.value
        self.__noClients = noClients
        self.__times = times[:]

        wholeTime = 0
        for t in times:
            wholeTime += t

        wholeTime = int(wholeTime)
        self.__wholeTime = wholeTime

        self.__timeS = wholeTime//1000 % 60
        self.__timeM = wholeTime//1000//60 % 60
        self.__timeH = wholeTime//1000//60//60

        self.clicker = 0


    def on_show(self):
        arcade.set_background_color(arcade.color.LIGHT_PINK)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self.clicker += 1
        if self.clicker == 2:
            self.window.show_view(MenuView())


    def on_draw(self):
        arcade.start_render()
        h = self.window.height
        drawText("Koniec gry", 400, h-10, 24)

        drawText(self.__text, 400, h-75, 16)
        drawText("Czas gry: {}h {}m {}s ({} klientów)"
                            .format(self.__timeH, self.__timeM, self.__timeS, self.__noClients-1),
                      400, h-125, 16
                     )

        for i in range( len(self.__times) ):
            ms = int(self.__times[i]) % 1000
            s =  int(self.__times[i])//1000 % 60
            m =  int(self.__times[i])//1000//60
            drawText("Klient {}: {}m {}s {}ms".format(i+1, m, s, ms), 400, h-(175+i*25), 12)