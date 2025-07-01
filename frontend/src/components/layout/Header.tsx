import navBarItems from "@/src/domain/constants/navBarItems"
import Link from "next/link"

const header = `flex flex-wrap items-center py-3 shadow-a-orange shadow-sm w-full`
const logo = `border-a-orange border-r-2 px-6 w-[100px]`
const link = `h-full px-6 py-3 text-center
hover:tracking-wider`

export default function Header(){
    return (
        <header className={header}>
            <img alt="logo" className={logo} src="/img/icon.png"/>

            {navBarItems.map(item => 
                <Link className={link} href={item.link} key={item.text}>{item.text}</Link>
            )}
        </header>
    )
}