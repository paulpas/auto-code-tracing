# colors.mk (new file)
RED    := \033[0;31m
GREEN  := \033[0;32m
YELLOW := \033[0;33m
BLUE   := \033[0;34m
PURPLE := \033[0;35m
CYAN   := \033[0;36m
WHITE  := \033[0;37m
BOLD   := \033[1m
NC     := \033[0m   # No Color

# helper function
define color_echo
	@printf "$(1)$(2)$(NC)\n"
endef
