import pygame
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class RenderManager:
    """Manages optimized rendering with sprite batching and dirty rectangles"""
    
    def __init__(self, screen, background_color=(50, 100, 50), ui_rects=None):
        self.screen = screen
        self.background_color = background_color
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # For sprite batching - group by texture
        self.batches = defaultdict(list)
        
        # For dirty rectangle rendering
        self.dirty_rects = []
        self.prev_entity_rects = {}  # Track previous frame entity positions
        
        # For viewport culling
        self.view_rect = pygame.Rect(0, 0, self.width, self.height)
        
        # UI rectangles to avoid overwriting
        self.ui_rects = ui_rects or []
        
        # Create background surface once
        self.background = self.create_background()
        
        # Track if this is the first frame
        self.first_frame = True
        
    def create_background(self):
        """Create the background grid surface once"""
        bg = pygame.Surface((self.width, self.height))
        bg.fill(self.background_color)
        
        # Draw grid lines
        for i in range(0, self.width, 100):
            pygame.draw.line(bg, (25, 65, 155), (i, 0), (i, self.height), 2)
        for i in range(0, self.height, 100):
            pygame.draw.line(bg, (25, 65, 155), (0, i), (self.width, i), 2)
            
        return bg
    
    def add_ui_rect(self, rect):
        """Add a UI rectangle to avoid drawing over"""
        self.ui_rects.append(rect)
    
    def remove_ui_rect(self, rect):
        """Remove a UI rectangle"""
        if rect in self.ui_rects:
            self.ui_rects.remove(rect)
    
    def add_to_batch(self, texture_id, position, source_rect=None, dest_rect=None):
        """Add sprite to appropriate batch based on texture"""
        if dest_rect is None:
            dest_rect = pygame.Rect(position[0], position[1], 
                                  source_rect.width if source_rect else 0, 
                                  source_rect.height if source_rect else 0)
        
        # Skip if completely outside viewport
        if not self.view_rect.colliderect(dest_rect):
            return
        
        # Skip if inside a UI rectangle
        for ui_rect in self.ui_rects:
            if ui_rect.colliderect(dest_rect):
                return
            
        # Add to appropriate batch
        self.batches[texture_id].append((source_rect, dest_rect))
        
        # Mark area as dirty
        self.dirty_rects.append(dest_rect.copy())
        
        # If entity existed before, mark its previous position as dirty too
        if texture_id in self.prev_entity_rects:
            prev_rect = self.prev_entity_rects[texture_id]
            self.dirty_rects.append(prev_rect)
        
        # Store current position for next frame
        self.prev_entity_rects[texture_id] = dest_rect.copy()
        
    def clear(self):
        """Reset batches for new frame"""
        self.batches.clear()
        
    def render(self):
        """Render all batched sprites efficiently"""
        # Always draw the full background on the first frame
        if self.first_frame:
            self.screen.blit(self.background, (0, 0))
            self.first_frame = False
            # Add the entire screen as a dirty rect for the first frame
            self.dirty_rects.append(pygame.Rect(0, 0, self.width, self.height))
        else:
            # Redraw background in dirty areas
            if self.dirty_rects:
                merged_rects = self._merge_rectangles(self.dirty_rects)
                for rect in merged_rects:
                    self.screen.blit(self.background, rect, rect)
            
        # Render each batch (grouped by texture)
        for texture_id, draw_info in self.batches.items():
            # Get the texture
            texture = texture_id[0]  # Assuming texture_id is (texture, extra_info)
            
            # Use more efficient blits for multiple sprites with same texture
            if len(draw_info) > 1:
                self.screen.blits([(texture, dest_rect, source_rect) 
                                 for source_rect, dest_rect in draw_info])
            elif draw_info:
                source_rect, dest_rect = draw_info[0]
                self.screen.blit(texture, dest_rect, source_rect)
        
        # Reset dirty rects for next frame
        self.dirty_rects = []
        
    def _merge_rectangles(self, rects, max_rects=10):
        """Merge overlapping rectangles to minimize redraw operations"""
        if not rects:
            return []
            
        # Start with a copy of the input rectangles
        result = [rect.copy() for rect in rects]
        
        # Simple greedy algorithm to merge rectangles
        i = 0
        while i < len(result) - 1 and len(result) > max_rects:
            j = i + 1
            while j < len(result):
                if result[i].colliderect(result[j]):
                    # Merge these rectangles
                    result[i].union_ip(result[j])
                    result.pop(j)
                else:
                    j += 1
            i += 1
            
        return result
