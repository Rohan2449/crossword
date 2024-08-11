import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                             letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # For every variable in our crossword puzzle
        for var in self.crossword:
            # for every domain in our variable
            for domain in self.domains[var]:
                # ensure that the domain's word length is consistent with the variable
                if len(domain) != var.length:
                    self.domains[var].remove(domain)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # if the length of the words are not the same, then there won't be any revisions to
        # their domains (since there is no overlap).
        if x.length != y.length:
            return False
        
        revision = False
        overlap = self.crossword.overlaps[x,y]
        # if there is an overlap between the two variables
        if overlap is not None:
            overlap_x = overlap[0]    # the index of the letter in x that overlaps with y
            overlap_y = overlap[1]    # the index of the letter in y that overlaps with x

            # for each word in the domain of x, if the word causes a conflict with the domain
            # of y, then remove the word from the domain of x
            for word_x in self.domains[x]:
                conflict = True

                for word_y in self.domains[y]:
                    # if the overlapping letters are the same, and the two words are different,
                    # then there is no conflict. Otherwise, there is a conflict and word_x must be
                    # removed from the domain of x.
                    if word_x[overlap_x] == word_y[overlap_y] and word_x != word_y:
                        conflict = False
                        break
                
                if conflict:
                    self.domains[x].remove(word_x)
                    revision = True
        else: # if there is no overlap between the two variables, then:
            # if there is only one value in the domain of y that is also in the domain of x,
            # then it should be removed form the domain of x
            if len(self.domains[y]) == 1 and self.domains[y][0] in self.domains[x]:
                self.domains[x].remove(self.domains[y][0])
                revision = True

        return revision



    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # if the list 'arcs' is empty, initialize it with the original constraints
        if arcs is None:
            arcs = []
            for var in self.crossword.variables:
                for neighbor in self.crossword.neighbors(var):
                    arcs.append( (var, neighbor) )
        

        # enforce arc consistency
        while len(arcs) != 0:
            (x,y) = arcs.pop(0)

            # if a revision was made to the domain, enforce arc consistency with the other
            # neighbors of x
            if self.revise(x,y):
                if len(self.domains[x]) == 0:
                    return False
                
                neighbors = self.crossword.neighbors(x).remove(y)
                for neighbor in neighbors:
                    arcs.append((x, neighbor))
            
        return True

        
    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in assignment:
            if assignment[var] is None:
                return False
        
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for var in assignment:
            if var is None:
                continue

            if len(assignment[var]) != var.length:
                return False
            # may need to check if two variables have the same assignment. ****
            for neighbor in self.crossword.neighbors(var):
                if neighbor is None:
                    continue

                overlap_var, overlap_neighbor = self.crossword.overlaps[var, neighbor]
                if assignment[var][overlap_var] != assignment[neighbor][overlap_neighbor]:
                    return False
                
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        rules_out = dict()
        for var_domain in self.domains[var]:
            conflict_count = 0

            for neighbor in self.crossword.neighbors(var):
                overlap_var, overlap_neighbor = self.crossword.overlaps[var, neighbor]
                if neighbor in assignment:
                    continue
                
                for neighbor_domain in self.domains[neighbor]:
                    if var_domain[overlap_var] != neighbor_domain[overlap_neighbor]:
                        conflict_count += 1
            
            rules_out[var_domain] = conflict_count

        return sorted(rules_out, key= lambda val: rules_out[val])



    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        least_domain_var = None
        equal_domain_var = None
        least_domain_count = 0

        # ensure that least_domain_var is assigned the variable with the smallest domain
        for var in self.crossword.variables:
            if var in assignment:
                continue
            # assign variable with smaller domain to least_domain_var, and forget about the var with equal domain length
            if len(self.domains[var]) < least_domain_count:
                least_domain_var = var
                least_domain_count = len(self.domains[var])
                equal_domain_var = None
            elif len(self.domains[var]) == least_domain_count:
                equal_domain_var = var

        if equal_domain_var is not None:
            # return the variable with the least degree (smallest number of neighbors)
            if len(self.crossword.neighbors(equal_domain_var)) > len(self.crossword.neighbors(least_domain_var)):
                return equal_domain_var


        return least_domain_var



    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        raise NotImplementedError


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
