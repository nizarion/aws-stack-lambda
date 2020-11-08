#!/usr/bin/env python3

from aws_cdk import core

from smartnumbers_test.smartnumbers_test_stack import SmartnumbersTestStack


app = core.App()
SmartnumbersTestStack(app, "smartnumbers-test")

app.synth()
