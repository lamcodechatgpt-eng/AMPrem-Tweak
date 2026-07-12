export TARGET = iphone:clang:latest:14.0
export ARCHS = arm64

include $(THEOS)/makefiles/common.mk

LIBRARY_NAME = AMPrem
AMPrem_FILES = Tweak.m
AMPrem_CFLAGS = -fobjc-arc
AMPrem_FRAMEWORKS = Foundation StoreKit

include $(THEOS_MAKE_PATH)/library.mk
