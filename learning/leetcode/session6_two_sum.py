"""
Leetcode Easy: Two Sum

Problem:
Given a list of integers and a target, return the indices of the two numbers
that add up to the target.

Learning point:
Use a dictionary to remember numbers we have already seen. This turns a nested
loop O(n^2) search into a single O(n) pass.
"""


def two_sum(nums, target):
    seen = {}
    for index, number in enumerate(nums):
        needed = target - number
        if needed in seen:
            return [seen[needed], index]
        seen[number] = index
    return []


def run_examples():
    examples = [
        ([2, 7, 11, 15], 9, [0, 1]),
        ([3, 2, 4], 6, [1, 2]),
        ([3, 3], 6, [0, 1]),
    ]
    for nums, target, expected in examples:
        actual = two_sum(nums, target)
        print(f"nums={nums}, target={target}, actual={actual}, expected={expected}")
        assert actual == expected


if __name__ == "__main__":
    run_examples()
