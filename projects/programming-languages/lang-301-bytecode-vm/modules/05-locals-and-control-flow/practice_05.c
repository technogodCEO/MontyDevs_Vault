// Practice for Module 05: Locals and Control Flow.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 5
//
// Replace each "Your code here" comment with your code. The checker compiles
// this file with the sanitizers on. Don't add a main() function.

#include <stdbool.h>
#include <stdint.h>

// 1. Two-byte operands, high byte first ("big-endian").
//    write_u16(code, 1, 0x1234) stores 0x12 in code[1] and 0x34 in code[2].
//    read_u16(code, 1) reads them back as 0x1234.
void write_u16(uint8_t *code, int offset, int value) {
  // Your code here
}

int read_u16(const uint8_t *code, int offset) {
  // Your code here
  return 0;
}

// 2. Patch a forward jump. The jump's two operand bytes are at
//    code[operand_offset] and code[operand_offset + 1]. When the VM has read
//    them, it's at operand_offset + 2, so the distance to store is
//    target - (operand_offset + 2). Store it with write_u16() and return
//    true, or return false (and store nothing) if it doesn't fit in 16 bits.
bool patch_jump(uint8_t *code, int operand_offset, int target) {
  // Your code here
  return false;
}

// 3. A tiny VM with jumps. It has one number, the counter, starting at 0.
//      OP_INC                       add 1 to the counter
//      OP_JUMP hi lo                jump FORWARD by the 16-bit distance hi lo
//      OP_LOOP_IF_LESS n hi lo      if the counter < n, jump BACKWARD by hi lo
//      OP_END                       stop, and return the counter
//    As in your VM, a distance counts from the byte just after the operands.
//    So in {OP_INC, OP_LOOP_IF_LESS, 5, 0, 5, OP_END}, the loop instruction
//    starts at 1, its operands end at 4, and jumping back 5 from 5 lands on
//    the OP_INC at 0. That program returns 5.
enum { OP_INC, OP_JUMP, OP_LOOP_IF_LESS, OP_END };

int run_counter(const uint8_t *code) {
  // Your code here
  return 0;
}

// 4. FIX THE BUG: an OP_LOOP instruction sits at op_offset, followed by its
//    two operand bytes. loop_distance() should return the distance to jump
//    back to loop_start. Every loop built with it ends up in the wrong place.
int loop_distance(int loop_start, int op_offset) {
  return op_offset - loop_start;
}
