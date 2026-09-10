# kitty-pounce

A [kitty terminal](https://sw.kovidgoyal.net/kitty/) extension that cycles
through every window, in every tab, in every OS window, as one flat ring --
one keypress moves forward or backward, wrapping from the last one back to
the first and vice versa.

## Origin

I run a lot of Claude Code agents at once, each in its own kitty window or
tab, and finding the right one again was getting harder as the count grew.
Kitty already has ways to move between windows, tabs and OS windows -- but
they're three separate keyboard shortcuts, each scoped to a different level,
so getting to "the next agent" meant picking the right shortcut for wherever
it happened to live.

The immediate trigger was hardware: my Jiffy 75 keyboard has two rotary
knobs. The right one is already spoken for -- volume and mute -- but the left
one had nothing bound to it. A flat, wrap-around ring was the obvious fit for
a knob: turn it one way or the other and step through every window, tab and
OS window as a single continuous list. That turned out to be a genuinely
faster way to find a specific agent than hunting through three separate
navigation shortcuts. (I still use kitty's own built-in `ctrl+shift+l` to
cycle layouts within an OS window -- a different axis entirely, which
kitty-pounce doesn't touch.)

kitty-pounce itself doesn't bind the knob -- see Installation below for
wiring up whichever key or device you like.

A quick terminology note: a split pane inside a tab -- made with kitty's
`new_window` action, bound by default to `kitty_mod+enter` -- is a kitty
**window**, not a tab. A **tab** is what you see in the tab bar at the top of
a kitty OS window. An **OS window** is an actual operating-system-level
window, which can hold several tabs, each of which can hold several windows.
kitty-pounce flattens all three levels: cycling visits every window in the
current tab first, then moves to the next tab's windows, then the next OS
window's, wrapping from the very last window back to the very first.

## Why would you want that?

kitty's built-in `next_window` / `previous_window` only cycle the windows in
the *current tab*, and `next_tab` / `previous_tab` only cycle the tabs in the
*current OS window*. With several tabs and OS windows open, there's no single
keystroke that walks every window everywhere -- you have to switch OS window,
then switch tab, then switch window, three different actions for what feels
like one motion.

kitty's own `select_tab` picker actually lists tabs from every OS window, but
silently fails to switch to most of them: it hands the list to
[`Boss.set_active_tab`](https://github.com/kovidgoyal/kitty/blob/v0.48.2/kitty/boss.py#L2782-L2786),
which only knows how to activate a tab inside the *currently focused* OS
window. kitty-pounce exists to fill that gap, one level deeper.

## Minimum requirements

Developed and verified against **kitty 0.48.2**. No lower bound is claimed
yet -- kitty's internal APIs are explicitly "neither entirely stable nor
documented" (see kitty's own [custom kittens
docs](https://sw.kovidgoyal.net/kitty/kittens/custom/)), so a minimum version
will be stated here once CI tests against more than one kitty release.

Requires Python >= 3.12 (kitty's own floor).

## Installation

Copy `pounce.py` into your kitty config directory:

```sh
curl -o ~/.config/kitty/pounce.py \
  https://raw.githubusercontent.com/garethparris/kitty-pounce/main/pounce.py
```

Then add to `~/.config/kitty/kitty.conf` (see `kitty.conf.example`):

```conf
map shift+page_down kitten pounce.py next
map shift+page_up   kitten pounce.py prev
```

Reload the config with `ctrl+shift+f5`, or restart kitty.

The key combination is entirely up to you -- kitty-pounce binds nothing on
its own, it only reads the direction (`next` or `prev`) passed on the `map`
line.

### Alternatively: clone it

If you keep your kitty config in a dotfiles repo, cloning in as a submodule
may suit you better than a loose file:

```sh
git clone https://github.com/garethparris/kitty-pounce.git ~/.config/kitty/kitty-pounce
```

and adjust the `map` lines to point at the cloned path:

```conf
map shift+page_down kitten kitty-pounce/pounce.py next
map shift+page_up   kitten kitty-pounce/pounce.py prev
```

## Limitations

- **`tab_bar_filter` is ignored.** If you've configured kitty's
  `tab_bar_filter`, kitty-pounce will still visit windows in tabs that filter
  hides from the tab bar -- it enumerates every tab kitty knows about, not
  just the visible ones.
- **A stacked/grouped set of windows sharing one on-screen position counts as
  a single stop**, landing on whichever one was last active there -- the same
  as kitty's own `next_window`/`previous_window`.
- **Crossing OS windows on different macOS Spaces triggers a Space switch.**
  kitty exposes no API for a kitten to know which Space an OS window is on,
  so there's no way to avoid this -- one keypress can trigger a full macOS
  Space-switch animation if the next window lives on another Space.

## License

[MIT](LICENSE)
