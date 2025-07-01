import Link from "next/link";

const container = `flex items-center justify-center pt-8`
const link = `!underline`

export default function page(){
    return (
        <div className={container}>
            <Link className={link} href='/'>
                Go back to Home
            </Link>
        </div>
    )
}