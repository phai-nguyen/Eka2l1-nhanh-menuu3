#!/usr/bin/env python3
"""HYBRIDHOME1: host-rendered S60 Home shell over the stable MENUUI36/Menu3 guest.

This experiment deliberately does NOT start the real Nokia Home UID 0x102750F0.
It keeps Menu3 (0x101F4CD2) alive inside EKA2L1, renders a lightweight Home
surface in the iOS frontend, and can launch real registered Symbian apps through
the existing EKA2L1 launcher bridge.
"""
from __future__ import annotations

import sys
from pathlib import Path

MARK = "HYBRIDHOME1-OLDOS-SHELL1"


def fail(msg: str) -> None:
    raise SystemExit(f"{MARK}: {msg}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_root(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "[HYBRIDHOME1][SHOW]" in text:
        return

    if "[M3HOME1][TRIGGER]" not in text:
        fail("HOMEONLY2/M3HOME1 baseline marker missing")
    if "0x101F4CD2u" not in text:
        fail("Menu3 UID baseline missing")

    prop_anchor = """@property (nonatomic, strong) NSMutableArray<NSString *> *pendingImportedFiles;
"""
    prop_repl = """@property (nonatomic, strong) NSMutableArray<NSString *> *pendingImportedFiles;

// HYBRIDHOME1 OLDOS-SHELL1: host-rendered Home surface.  The Symbian guest
// remains alive underneath; no ailaunch/Home process is started for this path.
@property (nonatomic, strong) UIView *hybridHomeView;
@property (nonatomic, strong) UILabel *hybridClockLabel;
"""
    text = replace_once(text, prop_anchor, prop_repl, "hybrid properties")

    chrome_anchor = """    // Forward hardware key/controller input to the guest only while a game runs; while the
    // homescreen apps list is up, the same keys drive its selection cursor instead.
    self.inputManager.enabled = self.gameRunning;
"""
    chrome_repl = """    // HYBRIDHOME1: when the host Home is visible it owns input.  Menu3 is still
    // executing underneath, but hardware/controller events must not leak into it.
    const BOOL hybridVisible = (self.hybridHomeView && !self.hybridHomeView.hidden);
    if (hybridVisible) {
        self.menuButton.hidden = YES;
        [self.view bringSubviewToFront:self.hybridHomeView];
    }

    // Forward hardware key/controller input to the guest only while a game runs and
    // the hybrid shell is not intercepting input.
    self.inputManager.enabled = self.gameRunning && !hybridVisible;
"""
    text = replace_once(text, chrome_anchor, chrome_repl, "input ownership")

    launch_anchor = """- (void)launchAppUid:(std::uint32_t)uid {
    self.currentGameUid = uid;
"""
    launch_repl = """- (void)launchAppUid:(std::uint32_t)uid {
    // Any real guest-app launch replaces the host shell surface.
    if (self.hybridHomeView && !self.hybridHomeView.hidden) {
        self.hybridHomeView.hidden = YES;
    }
    self.currentGameUid = uid;
"""
    text = replace_once(text, launch_anchor, launch_repl, "launch cleanup")

    menu_anchor = """    GameMenuView *menu = [[GameMenuView alloc] initWithTitle:EKAL(@"Game Menu")];
    [menu addOption:EKAL(@"Switch Key Layout") destructive:NO handler:^{ [self showLayoutChooserController]; }];

    // M3HOME1 HOMEBRIDGE1: the successful device path is normal/HLE EKA2L1 with
"""
    menu_repl = """    GameMenuView *menu = [[GameMenuView alloc] initWithTitle:EKAL(@"Game Menu")];
    [menu addOption:EKAL(@"Switch Key Layout") destructive:NO handler:^{ [self showLayoutChooserController]; }];

    // HYBRIDHOME1 OLDOS-SHELL1: keep the validated Menu3 guest alive and put a
    // host-rendered S60 Home surface above it.  This path intentionally never
    // launches Nokia Home UID 0x102750F0.
    if (self.currentGameUid == 0x101F4CD2u) {
        [menu addOption:@"Hybrid Home (thử nghiệm)" destructive:NO handler:^{
            NSLog(@"[HYBRIDHOME1][TRIGGER] source_uid=0x101F4CD2 real_home_started=0");
            dispatch_async(dispatch_get_main_queue(), ^{
                [self showHybridHome];
            });
        }];
    }

    // M3HOME1 HOMEBRIDGE1: the successful device path is normal/HLE EKA2L1 with
"""
    text = replace_once(text, menu_anchor, menu_repl, "Menu3 hybrid action")

    methods_anchor = """// ---- Launch / exit --------------------------------------------------------
"""
    methods = r'''// ---- HYBRIDHOME1 host shell -----------------------------------------------

- (void)setupHybridHomeIfNeeded {
    if (self.hybridHomeView) {
        return;
    }

    UIView *home = [[UIView alloc] initWithFrame:self.view.bounds];
    home.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    home.backgroundColor = [UIColor colorWithRed:0.08 green:0.12 blue:0.14 alpha:1.0];
    home.hidden = YES;
    home.accessibilityIdentifier = @"HYBRIDHOME1";

    UILabel *carrier = [[UILabel alloc] init];
    carrier.translatesAutoresizingMaskIntoConstraints = NO;
    carrier.text = @"Viettel";
    carrier.textColor = [UIColor whiteColor];
    carrier.font = [UIFont systemFontOfSize:15 weight:UIFontWeightSemibold];

    UILabel *clock = [[UILabel alloc] init];
    clock.translatesAutoresizingMaskIntoConstraints = NO;
    clock.textColor = [UIColor whiteColor];
    clock.textAlignment = NSTextAlignmentRight;
    clock.font = [UIFont monospacedDigitSystemFontOfSize:15 weight:UIFontWeightSemibold];
    self.hybridClockLabel = clock;

    UILabel *title = [[UILabel alloc] init];
    title.translatesAutoresizingMaskIntoConstraints = NO;
    title.text = @"Nokia 5800 · Hybrid Home";
    title.textColor = [UIColor whiteColor];
    title.textAlignment = NSTextAlignmentCenter;
    title.font = [UIFont systemFontOfSize:24 weight:UIFontWeightBold];

    UILabel *detail = [[UILabel alloc] init];
    detail.translatesAutoresizingMaskIntoConstraints = NO;
    detail.text = @"Home do EKA2L1 dựng\nMenu3 và ứng dụng Symbian vẫn chạy thật";
    detail.textColor = [UIColor colorWithWhite:0.86 alpha:1.0];
    detail.textAlignment = NSTextAlignmentCenter;
    detail.numberOfLines = 0;
    detail.font = [UIFont systemFontOfSize:15];

    UIButton *apps = [UIButton buttonWithType:UIButtonTypeSystem];
    apps.translatesAutoresizingMaskIntoConstraints = NO;
    [apps setTitle:@"Ứng dụng Symbian thật" forState:UIControlStateNormal];
    [apps setTitleColor:[UIColor whiteColor] forState:UIControlStateNormal];
    apps.titleLabel.font = [UIFont systemFontOfSize:17 weight:UIFontWeightSemibold];
    apps.backgroundColor = [UIColor colorWithWhite:1.0 alpha:0.14];
    apps.layer.cornerRadius = 12.0;
    [apps addTarget:self action:@selector(showHybridAppChooser) forControlEvents:UIControlEventTouchUpInside];

    UIButton *menu3 = [UIButton buttonWithType:UIButtonTypeSystem];
    menu3.translatesAutoresizingMaskIntoConstraints = NO;
    [menu3 setTitle:@"Trở về Menu3 thật" forState:UIControlStateNormal];
    [menu3 setTitleColor:[UIColor whiteColor] forState:UIControlStateNormal];
    menu3.titleLabel.font = [UIFont systemFontOfSize:17 weight:UIFontWeightSemibold];
    menu3.backgroundColor = [UIColor colorWithWhite:1.0 alpha:0.10];
    menu3.layer.cornerRadius = 12.0;
    [menu3 addTarget:self action:@selector(hideHybridHome) forControlEvents:UIControlEventTouchUpInside];

    UILabel *note = [[UILabel alloc] init];
    note.translatesAutoresizingMaskIntoConstraints = NO;
    note.text = @"HYBRIDHOME1 · không khởi chạy Home UID 0x102750F0";
    note.textColor = [UIColor colorWithWhite:0.70 alpha:1.0];
    note.textAlignment = NSTextAlignmentCenter;
    note.numberOfLines = 0;
    note.font = [UIFont systemFontOfSize:12];

    [home addSubview:carrier];
    [home addSubview:clock];
    [home addSubview:title];
    [home addSubview:detail];
    [home addSubview:apps];
    [home addSubview:menu3];
    [home addSubview:note];

    [NSLayoutConstraint activateConstraints:@[
        [carrier.leadingAnchor constraintEqualToAnchor:home.safeAreaLayoutGuide.leadingAnchor constant:18],
        [carrier.topAnchor constraintEqualToAnchor:home.safeAreaLayoutGuide.topAnchor constant:10],
        [clock.trailingAnchor constraintEqualToAnchor:home.safeAreaLayoutGuide.trailingAnchor constant:-18],
        [clock.centerYAnchor constraintEqualToAnchor:carrier.centerYAnchor],

        [title.leadingAnchor constraintEqualToAnchor:home.leadingAnchor constant:20],
        [title.trailingAnchor constraintEqualToAnchor:home.trailingAnchor constant:-20],
        [title.centerYAnchor constraintEqualToAnchor:home.centerYAnchor constant:-100],

        [detail.leadingAnchor constraintEqualToAnchor:home.leadingAnchor constant:28],
        [detail.trailingAnchor constraintEqualToAnchor:home.trailingAnchor constant:-28],
        [detail.topAnchor constraintEqualToAnchor:title.bottomAnchor constant:14],

        [apps.centerXAnchor constraintEqualToAnchor:home.centerXAnchor],
        [apps.topAnchor constraintEqualToAnchor:detail.bottomAnchor constant:34],
        [apps.widthAnchor constraintEqualToConstant:250],
        [apps.heightAnchor constraintEqualToConstant:52],

        [menu3.centerXAnchor constraintEqualToAnchor:home.centerXAnchor],
        [menu3.topAnchor constraintEqualToAnchor:apps.bottomAnchor constant:14],
        [menu3.widthAnchor constraintEqualToConstant:250],
        [menu3.heightAnchor constraintEqualToConstant:52],

        [note.leadingAnchor constraintEqualToAnchor:home.leadingAnchor constant:24],
        [note.trailingAnchor constraintEqualToAnchor:home.trailingAnchor constant:-24],
        [note.bottomAnchor constraintEqualToAnchor:home.safeAreaLayoutGuide.bottomAnchor constant:-18]
    ]];

    self.hybridHomeView = home;
    [self.view addSubview:home];
}

- (void)showHybridHome {
    if (!self.gameRunning || self.currentGameUid != 0x101F4CD2u) {
        NSLog(@"[HYBRIDHOME1][GUARD_REJECT] gameRunning=%d uid=0x%08X",
              (int)self.gameRunning, self.currentGameUid);
        return;
    }

    [self setupHybridHomeIfNeeded];

    NSDateFormatter *fmt = [[NSDateFormatter alloc] init];
    fmt.dateFormat = @"HH:mm";
    self.hybridClockLabel.text = [fmt stringFromDate:[NSDate date]];

    self.hybridHomeView.hidden = NO;
    self.menuButton.hidden = YES;
    self.inputManager.enabled = NO;
    [self.view bringSubviewToFront:self.hybridHomeView];

    NSLog(@"[HYBRIDHOME1][SHOW] source_uid=0x101F4CD2 guest_menu3_alive=1 real_home_started=0");
}

- (void)hideHybridHome {
    if (!self.hybridHomeView || self.hybridHomeView.hidden) {
        return;
    }
    self.hybridHomeView.hidden = YES;
    NSLog(@"[HYBRIDHOME1][RETURN_MENU3] uid=0x101F4CD2 guest_menu3_alive=1");
    [self updateChrome];
}

- (void)showHybridAppChooser {
    std::vector<eka2l1::ios::bridge::app_entry> apps = eka2l1::ios::bridge::get_apps();
    NSMutableArray<NSDictionary *> *choices = [NSMutableArray array];
    NSMutableSet<NSNumber *> *seen = [NSMutableSet set];

    for (auto &app : apps) {
        // Keep the comparison path deterministic: do not offer Menu3 itself or the
        // real Nokia Home process from the hybrid launcher.
        if (app.uid == 0x101F4CD2u || app.uid == 0x102750F0u) {
            continue;
        }

        NSNumber *uidNum = @(app.uid);
        if ([seen containsObject:uidNum]) {
            continue;
        }
        [seen addObject:uidNum];

        NSString *name = app.name.empty()
            ? [NSString stringWithFormat:@"0x%08X", app.uid]
            : [NSString stringWithUTF8String:app.name.c_str()];
        if (name.length == 0) {
            name = [NSString stringWithFormat:@"0x%08X", app.uid];
        }
        [choices addObject:@{ @"uid": uidNum, @"name": name }];
        if (choices.count >= 12) {
            break;
        }
    }

    NSLog(@"[HYBRIDHOME1][APP_CHOOSER] visible_choices=%lu real_home_uid_excluded=1",
          (unsigned long)choices.count);

    if (choices.count == 0) {
        UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"Hybrid Home"
            message:@"Chưa có ứng dụng Symbian nào sẵn sàng để khởi chạy."
            preferredStyle:UIAlertControllerStyleAlert];
        [alert addAction:[UIAlertAction actionWithTitle:@"Đóng" style:UIAlertActionStyleCancel handler:nil]];
        [self presentViewController:alert animated:YES completion:nil];
        return;
    }

    UIAlertController *sheet = [UIAlertController alertControllerWithTitle:@"Ứng dụng Symbian thật"
        message:@"Chọn một ứng dụng đã đăng ký trong AppArc/EKA2L1."
        preferredStyle:UIAlertControllerStyleActionSheet];

    for (NSDictionary *entry in choices) {
        const std::uint32_t uid = (std::uint32_t)[entry[@"uid"] unsignedLongValue];
        NSString *name = entry[@"name"];
        [sheet addAction:[UIAlertAction actionWithTitle:name style:UIAlertActionStyleDefault
            handler:^(UIAlertAction *action) {
                NSLog(@"[HYBRIDHOME1][LAUNCH_REAL_APP] uid=0x%08X name=%@", uid, name);
                self.hybridHomeView.hidden = YES;
                [self launchAppUid:uid];
            }]];
    }

    [sheet addAction:[UIAlertAction actionWithTitle:@"Huỷ" style:UIAlertActionStyleCancel handler:nil]];
    sheet.popoverPresentationController.sourceView = self.hybridHomeView;
    sheet.popoverPresentationController.sourceRect =
        CGRectMake(CGRectGetMidX(self.hybridHomeView.bounds), CGRectGetMidY(self.hybridHomeView.bounds), 1, 1);
    [self presentViewController:sheet animated:YES completion:nil];
}

''' + methods_anchor
    text = replace_once(text, methods_anchor, methods, "hybrid methods")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_hybridhome1_oldosshell.py <upstream-root>")

    upstream = Path(sys.argv[1]).resolve()
    root = upstream / "src/emu/ios/app/RootViewController.mm"
    if not root.is_file():
        fail("RootViewController.mm missing")

    patch_root(root)

    out = root.read_text(encoding="utf-8")
    required = (
        "[HYBRIDHOME1][TRIGGER]",
        "[HYBRIDHOME1][SHOW]",
        "[HYBRIDHOME1][RETURN_MENU3]",
        "[HYBRIDHOME1][APP_CHOOSER]",
        "[HYBRIDHOME1][LAUNCH_REAL_APP]",
        "Hybrid Home (thử nghiệm)",
        "guest_menu3_alive=1",
        "real_home_started=0",
        "eka2l1::ios::bridge::get_apps()",
    )
    for needle in required:
        if needle not in out:
            fail(f"post-apply marker missing: {needle}")

    print(f"{MARK}: applied")
    print("baseline=HOMEONLY2_MENUUI36_NOJAVA_MANIC3")
    print("source_guest=MENU3_UID_0x101F4CD2")
    print("presentation=HOST_UIKIT")
    print("real_home_uid_0x102750F0=NOT_STARTED")
    print("registered_apps=EKA2L1_BRIDGE_GET_APPS")
    print("real_app_launch=EKA2L1_EXISTING_LAUNCHER")
    print("nativeboot=ABSENT")
    print("compatboot=ABSENT")


if __name__ == "__main__":
    main()
