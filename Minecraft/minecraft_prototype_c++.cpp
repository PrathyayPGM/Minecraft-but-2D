#include <SFML/Graphics.hpp>
#include <vector>
#include <memory>
#include <cmath>
#include <string>
#include <unordered_map>
#include <iostream>

// Constants
const int WIDTH = 1000;
const int HEIGHT = 800;
const sf::Color BLACK(0, 0, 0);
const sf::Color WHITE(255, 255, 255);
const sf::Color SKY_BLUE(135, 206, 235);
const int MAX_FALL_DISTANCE = 1000;
const int BLOCK_HEALTH = 100;

// Hotbar constants
const int HOTBAR_SLOTS = 9;
const int SLOT_SIZE = 40;
const int HOTBAR_WIDTH = HOTBAR_SLOTS * SLOT_SIZE;
const int HOTBAR_HEIGHT = SLOT_SIZE;
const int HOTBAR_MARGIN = 10;
const sf::Color SELECTED_COLOR(255, 255, 0);

// Block types
enum class BlockType { GRASS, DIRT, STONE };

// Forward declarations
class Block;
class Player;

class Camera {
public:
    sf::View view;
    int width, height;

    Camera(int w, int h) : width(w), height(h) {
        view.setSize(w, h);
        view.setCenter(w / 2, h / 2);
    }

    void apply(sf::Transformable& entity) {
        // SFML views handle this automatically during drawing
    }

    void update(const Player& target);
};

class Block {
protected:
    sf::Vector2f position;
    std::shared_ptr<sf::Texture> texture;
    sf::Sprite sprite;
    BlockType type;

public:
    sf::FloatRect rect;

    Block(float x, float y, BlockType t) : position(x, y), type(t) {
        rect.left = x;
        rect.top = y;
        rect.width = 50;
        rect.height = 50;
    }

    virtual bool loadTexture() {
        return false;
    }

    void draw(sf::RenderWindow& window, const Camera& camera) {
        sprite.setPosition(position.x - camera.view.getCenter().x + camera.width/2,
                          position.y - camera.view.getCenter().y + camera.height/2);
        window.draw(sprite);
    }

    BlockType getType() const { return type; }
};

class GrassBlock : public Block {
public:
    GrassBlock(float x, float y) : Block(x, y, BlockType::GRASS) {
        if (!loadTexture()) {
            sprite.setTextureRect(sf::IntRect(0, 0, 50, 50));
            sprite.setColor(sf::Color::Green);
        }
    }

    bool loadTexture() override {
        texture = std::make_shared<sf::Texture>();
        if (texture->loadFromFile("textures/grass.png")) {
            texture->setSmooth(true);
            sprite.setTexture(*texture);
            sprite.setScale(50.0f / texture->getSize().x, 50.0f / texture->getSize().y);
            return true;
        }
        return false;
    }
};

class DirtBlock : public Block {
public:
    DirtBlock(float x, float y) : Block(x, y, BlockType::DIRT) {
        if (!loadTexture()) {
            sprite.setTextureRect(sf::IntRect(0, 0, 50, 50));
            sprite.setColor(sf::Color(139, 69, 19));
        }
    }

    bool loadTexture() override {
        texture = std::make_shared<sf::Texture>();
        if (texture->loadFromFile("textures/dirt.png")) {
            texture->setSmooth(true);
            sprite.setTexture(*texture);
            sprite.setScale(50.0f / texture->getSize().x, 50.0f / texture->getSize().y);
            return true;
        }
        return false;
    }
};

class StoneBlock : public Block {
public:
    StoneBlock(float x, float y) : Block(x, y, BlockType::STONE) {
        if (!loadTexture()) {
            sprite.setTextureRect(sf::IntRect(0, 0, 50, 50));
            sprite.setColor(sf::Color(128, 128, 128));
        }
    }

    bool loadTexture() override {
        texture = std::make_shared<sf::Texture>();
        if (texture->loadFromFile("textures/stone.png")) {
            texture->setSmooth(true);
            sprite.setTexture(*texture);
            sprite.setScale(50.0f / texture->getSize().x, 50.0f / texture->getSize().y);
            return true;
        }
        return false;
    }
};

class Player {
private:
    sf::Vector2f worldPos;
    sf::Texture texture;
    sf::Sprite sprite;
    float jumpPower = -20;
    float gravity = 0;
    sf::FloatRect rect;
    bool onGround = false;
    float speed = 5;
    int jumpCooldown = 0;
    bool facingRight = true;
    int health = 10;
    int damageFrames = 0;
    int damageDelay = 30;
    int selectedSlot = 0;
    float miningProgress = 0;
    float miningSpeed = 1;
    float maxMineDistance = 250;
    Block* miningBlock = nullptr;

    struct InventorySlot {
        BlockType type;
        int count;
    };

    std::vector<InventorySlot> inventory;

public:
    Player() {
        rect.width = 50;
        rect.height = 150;
        worldPos.x = 500;
        worldPos.y = HEIGHT - 200;
        rect.left = worldPos.x;
        rect.top = worldPos.y;

        inventory.resize(HOTBAR_SLOTS);
        for (auto& slot : inventory) {
            slot.type = BlockType::GRASS; // Default to grass for testing
            slot.count = 0;
        }

        if (!texture.loadFromFile("textures/steve.png")) {
            sprite.setTextureRect(sf::IntRect(0, 0, 50, 150));
            sprite.setColor(sf::Color::Red);
        } else {
            sprite.setTexture(texture);
            sprite.setScale(50.0f / texture.getSize().x, 150.0f / texture.getSize().y);
        }
    }

    void update(const std::vector<std::unique_ptr<Block>>& groundBlocks) {
        // Update position
        rect.left = worldPos.x;
        rect.top = worldPos.y;
        
        // Apply gravity
        worldPos.y += gravity;
        gravity += 0.8f;

        // Check collisions
        onGround = false;
        for (const auto& block : groundBlocks) {
            if (rect.intersects(block->rect)) {
                // Landing on top
                if (gravity > 0 && rect.top + rect.height > block->rect.top) {
                    worldPos.y = block->rect.top - rect.height;
                    rect.top = block->rect.top - rect.height;
                    gravity = 0;
                    onGround = true;
                }
                // Hitting head
                else if (gravity < 0 && rect.top < block->rect.top + block->rect.height) {
                    worldPos.y = block->rect.top + block->rect.height;
                    rect.top = block->rect.top + block->rect.height;
                    gravity = 0;
                }
            }
        }

        // Jump buffer system
        if (onGround) {
            jumpCooldown = 5;
        } else if (jumpCooldown > 0) {
            jumpCooldown--;
        }
    }

    void draw(sf::RenderWindow& window, const Camera& camera) {
        sprite.setPosition(rect.left - camera.view.getCenter().x + camera.width/2,
                         rect.top - camera.view.getCenter().y + camera.height/2);
        if (!facingRight) {
            sprite.setScale(-50.0f / texture.getSize().x, 150.0f / texture.getSize().y);
            sprite.setPosition(rect.left + rect.width - camera.view.getCenter().x + camera.width/2,
                             rect.top - camera.view.getCenter().y + camera.height/2);
        } else {
            sprite.setScale(50.0f / texture.getSize().x, 150.0f / texture.getSize().y);
        }
        window.draw(sprite);
    }

    void moveLeft() {
        worldPos.x -= speed;
        facingRight = false;
    }

    void moveRight() {
        worldPos.x += speed;
        facingRight = true;
    }

    void jump() {
        if (onGround || jumpCooldown > 0) {
            gravity = jumpPower;
        }
    }

    const sf::Vector2f& getPosition() const { return worldPos; }
    const sf::FloatRect& getRect() const { return rect; }
    int getSelectedSlot() const { return selectedSlot; }
    void setSelectedSlot(int slot) { selectedSlot = slot; }
    const std::vector<InventorySlot>& getInventory() const { return inventory; }
};

void Camera::update(const Player& target) {
    view.setCenter(target.getPosition().x, target.getPosition().y - 50); // Slight offset
}

void drawHotbar(sf::RenderWindow& window, const Player& player) {
    // Calculate hotbar position (centered at bottom)
    float hotbarX = (WIDTH - HOTBAR_WIDTH) / 2.0f;
    float hotbarY = HEIGHT - HOTBAR_HEIGHT - HOTBAR_MARGIN;
    
    // Draw hotbar background
    sf::RectangleShape background(sf::Vector2f(HOTBAR_WIDTH + 4, HOTBAR_HEIGHT + 4));
    background.setPosition(hotbarX - 2, hotbarY - 2);
    background.setFillColor(sf::Color(50, 50, 50));
    window.draw(background);

    sf::RectangleShape hotbar(sf::Vector2f(HOTBAR_WIDTH, HOTBAR_HEIGHT));
    hotbar.setPosition(hotbarX, hotbarY);
    hotbar.setFillColor(sf::Color(150, 150, 150));
    window.draw(hotbar);
    
    // Draw slots
    for (int slot = 0; slot < HOTBAR_SLOTS; ++slot) {
        float slotX = hotbarX + slot * SLOT_SIZE;
        sf::RectangleShape slotRect(sf::Vector2f(SLOT_SIZE - 4, SLOT_SIZE - 4));
        slotRect.setPosition(slotX + 2, hotbarY + 2);
        slotRect.setOutlineThickness(2);
        slotRect.setOutlineColor(sf::Color(100, 100, 100));
        slotRect.setFillColor(sf::Color::Transparent);
        window.draw(slotRect);
        
        // Draw item in slot
        const auto& item = player.getInventory()[slot];
        if (item.count > 0) {
            sf::RectangleShape itemIcon(sf::Vector2f(SLOT_SIZE - 10, SLOT_SIZE - 10));
            itemIcon.setPosition(slotX + 5, hotbarY + 5);
            
            switch (item.type) {
                case BlockType::DIRT:
                    itemIcon.setFillColor(sf::Color(139, 69, 19));
                    break;
                case BlockType::STONE:
                    itemIcon.setFillColor(sf::Color(128, 128, 128));
                    break;
                case BlockType::GRASS:
                    itemIcon.setFillColor(sf::Color::Green);
                    break;
            }
            window.draw(itemIcon);
            
            // Draw item count
            sf::Font font;
            if (font.loadFromFile("arial.ttf")) {
                sf::Text countText(std::to_string(item.count), font, 20);
                countText.setPosition(slotX + SLOT_SIZE - 20, hotbarY + SLOT_SIZE - 25);
                countText.setFillColor(WHITE);
                window.draw(countText);
            }
        }
    }
    
    // Draw selection indicator
    float selectionX = hotbarX + player.getSelectedSlot() * SLOT_SIZE;
    sf::RectangleShape selection(sf::Vector2f(SLOT_SIZE + 4, SLOT_SIZE + 4));
    selection.setPosition(selectionX - 2, hotbarY - 2);
    selection.setOutlineThickness(2);
    selection.setOutlineColor(SELECTED_COLOR);
    selection.setFillColor(sf::Color::Transparent);
    window.draw(selection);
}

int main() {
    sf::RenderWindow window(sf::VideoMode(WIDTH, HEIGHT), "Yearn for the Mines");
    window.setFramerateLimit(60);

    // Initialize game objects
    Player player;
    std::vector<std::unique_ptr<Block>> groundBlocks;
    Camera camera(WIDTH, HEIGHT);

    // Create world with layers
    for (int x = -WIDTH; x < WIDTH * 10; x += 50) {
        groundBlocks.emplace_back(std::make_unique<GrassBlock>(x, HEIGHT - 50));
        groundBlocks.emplace_back(std::make_unique<DirtBlock>(x, HEIGHT));
        groundBlocks.emplace_back(std::make_unique<DirtBlock>(x, HEIGHT + 50));
        for (int y = HEIGHT + 100; y < HEIGHT + (50 * 50); y += 50) {
            groundBlocks.emplace_back(std::make_unique<StoneBlock>(x, y));
        }
    }

    // Main game loop
    while (window.isOpen()) {
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) {
                window.close();
            }
            
            if (event.type == sf::Event::KeyPressed) {
                if (event.key.code == sf::Keyboard::Space) {
                    player.jump();
                }
                
                // Number keys (1-9) select slots
                if (event.key.code >= sf::Keyboard::Num1 && event.key.code <= sf::Keyboard::Num9) {
                    player.setSelectedSlot(event.key.code - sf::Keyboard::Num1);
                }
            }
            
            if (event.type == sf::Event::MouseWheelScrolled) {
                if (event.mouseWheelScroll.delta > 0) { // Wheel up
                    player.setSelectedSlot((player.getSelectedSlot() - 1 + HOTBAR_SLOTS) % HOTBAR_SLOTS);
                } else if (event.mouseWheelScroll.delta < 0) { // Wheel down
                    player.setSelectedSlot((player.getSelectedSlot() + 1) % HOTBAR_SLOTS);
                }
            }
        }

        // Movement controls
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Left)) {
            player.moveLeft();
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Right)) {
            player.moveRight();
        }

        // Update game state
        player.update(groundBlocks);
        camera.update(player);

        // Drawing
        window.clear(SKY_BLUE);
        
        // Set the camera view
        window.setView(camera.view);
        
        // Draw blocks
        for (const auto& block : groundBlocks) {
            block->draw(window, camera);
        }
        
        // Draw player
        player.draw(window, camera);
        
        // Reset the view for UI elements
        window.setView(window.getDefaultView());
        
        // Draw hotbar
        drawHotbar(window, player);
        
        window.display();
    }

    return 0;
}