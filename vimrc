" Replace the following with path to the script
let g:browsersync="./browser-code-sync.py"
function! BrowserSyncPull()
	let l:idx=bufnr('%')-1
	execute '%!' . g:browsersync . ' pull - ' . l:idx . ' \r'
endfunction
function! BrowserSyncPush()
	let l:idx=bufnr('%')-1
	execute 'w !' . g:browsersync . ' push - ' . l:idx . ' \r'
endfunction
" " Push to browser
map <silent><C-H> <esc>:call BrowserSyncPush()<CR><CR>
" Pull from browser
map <silent><C-L> <esc>:call BrowserSyncPull()<CR><CR>
" " Submit on freecodecamp
map <silent><C-J> <esc>:execute '!' . g:browsersync . ' execjs "document.getElementById(\"submitButton\").click()"'<CR><CR>
" " Next challenge on freecodecamp
map <silent><C-K> <esc>:execute '!' . g:browsersync . ' execjs "document.getElementById(\"next-challenge\").click()"'<CR><CR>
